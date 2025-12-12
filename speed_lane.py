import cv2 as cv
import numpy as np
import torch
import time
from ultralytics import YOLO
from sort.sort import Sort
from utils import map_car, read_license_plate
from flask import Flask, Response

app = Flask(__name__)

# --- CONFIGURATION ---
# Lane 1 (Further/Upper)
LINE_1_Y = 1100
L1_X_START, L1_X_END = 800, 1900  # <--- Adjust these to change length

# Lane 2 (Closer/Lower)
LINE_2_Y = 1550
L2_X_START, L2_X_END = 1900, 3000  # <--- Adjust these to change length

OFFSET = 20              
PIXELS_PER_METER = 10    
TARGET_FPS = 30          

# --- LOAD MODELS ---
device = 'cuda' if torch.cuda.is_available() else 'cpu'
vehicle_model = YOLO('yolov8n.pt').to(device)
plate_model = YOLO('./models/license_plate_detector.pt').to(device)
mot_tracker = Sort()

class_names = {2: 'Car', 3: 'Bike', 5: 'Bus', 7: 'Truck'}
vehicle_classes = list(class_names.keys())

def get_closest_vehicle_type(tracked_box, original_detections):
    tx1, ty1, tx2, ty2 = tracked_box
    t_center = ((tx1 + tx2) / 2, (ty1 + ty2) / 2)
    closest_class = "Unknown"
    min_dist = float('inf')
    for d in original_detections:
        ox1, oy1, ox2, oy2 = d[:4]
        o_center = ((ox1 + ox2) / 2, (oy1 + oy2) / 2)
        dist = (t_center[0] - o_center[0])**2 + (t_center[1] - o_center[1])**2
        if dist < min_dist and dist < 2000: 
            min_dist = dist
            closest_class = class_names.get(int(d[5]), "Vehicle")
    return closest_class

def draw_lane_dashboard(frame, title, stats, x_pos, y_pos, color):
    bw, bh = 400, 260
    overlay = frame.copy()
    cv.rectangle(overlay, (x_pos, y_pos), (x_pos + bw, y_pos + bh), (0, 0, 0), -1)
    cv.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    cv.rectangle(frame, (x_pos, y_pos), (x_pos + bw, y_pos + bh), color, 2)
    cv.putText(frame, title, (x_pos + 15, y_pos + 40), cv.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
    cv.putText(frame, f"TOTAL: {stats['total']}", (x_pos + 15, y_pos + 90), cv.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    curr_y = y_pos + 135
    for v_type in ['Car', 'Bike', 'Bus', 'Truck']:
        cv.putText(frame, f"{v_type}: {stats[v_type]}", (x_pos + 15, curr_y), cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
        curr_y += 30

def generate_frames():
    video_path = './1.mp4' 
    cap = cv.VideoCapture(video_path)
    
    lane_stats = {
        'Lane 1': {'total': 0, 'Car': 0, 'Bike': 0, 'Bus': 0, 'Truck': 0},
        'Lane 2': {'total': 0, 'Car': 0, 'Bike': 0, 'Bus': 0, 'Truck': 0}
    }
    
    counted_ids = set()
    car_memory = {} 
    frame_nmr = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv.CAP_PROP_POS_FRAMES, 0)
            continue
        
        frame_nmr += 1
        vehicles = vehicle_model(frame, verbose=False)[0]
        detections_ = []
        raw_detections = [] 
        for box in vehicles.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = box
            if int(class_id) in vehicle_classes:
                detections_.append([x1, y1, x2, y2, score])
                raw_detections.append([x1, y1, x2, y2, score, class_id])

        if len(detections_) > 0:
            track_ids = mot_tracker.update(np.asarray(detections_))
        else:
            track_ids = np.empty((0, 5))

        plates = plate_model(frame, verbose=False)[0]
        
        for track in track_ids:
            x1, y1, x2, y2, car_id = track
            car_id = int(car_id)
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)

            if car_id not in car_memory:
                car_memory[car_id] = {'text': 'Scanning...', 'type': 'Vehicle', 'box': [x1,y1,x2,y2],
                                      'last_y': cy, 'current_speed': 0, 'captured_speed': None}

            if car_memory[car_id]['type'] == 'Vehicle':
                car_memory[car_id]['type'] = get_closest_vehicle_type([x1, y1, x2, y2], raw_detections)
            
            # Speed calculation
            if frame_nmr % 5 == 0:
                speed_kmh = ((abs(cy - car_memory[car_id]['last_y']) / PIXELS_PER_METER) / (5 / TARGET_FPS)) * 3.6
                if speed_kmh > 2: car_memory[car_id]['current_speed'] = int(speed_kmh)
                car_memory[car_id]['last_y'] = cy

            car_memory[car_id]['box'] = [x1, y1, x2, y2]
            car_memory[car_id]['last_seen'] = frame_nmr

            # --- UPDATED CROSSING LOGIC (WITH X-RANGE CHECK) ---
            lane_configs = [
                ('Lane 1', LINE_1_Y, L1_X_START, L1_X_END, (255, 100, 0)),
                ('Lane 2', LINE_2_Y, L2_X_START, L2_X_END, (0, 100, 255))
            ]
            
            for name, ly, lx_start, lx_end, l_color in lane_configs:
                # Check if center Y is at line AND center X is within line length
                if (ly - OFFSET < cy < ly + OFFSET) and (lx_start < cx < lx_end):
                    if car_id not in counted_ids:
                        car_memory[car_id]['captured_speed'] = car_memory[car_id]['current_speed']
                        v_type = car_memory[car_id]['type']
                        lane_stats[name]['total'] += 1
                        if v_type in lane_stats[name]: lane_stats[name][v_type] += 1
                        counted_ids.add(car_id)
                        # Flash line green
                        cv.line(frame, (lx_start, ly), (lx_end, ly), (0, 255, 0), 12)

        # 5. OCR
        for plate in plates.boxes.data.tolist():
            px1, py1, px2, py2, _, _ = plate
            _, _, _, _, car_id = map_car(plate, track_ids)
            if car_id != -1 and car_id in car_memory:
                if (car_memory[car_id]['text'] == 'Scanning...' or frame_nmr % 20 == 0):
                    crop = frame[int(py1):int(py2), int(px1):int(px2), :]
                    if crop.size > 0:
                        try:
                            gray = cv.cvtColor(crop, cv.COLOR_BGR2GRAY)
                            _, thresh = cv.threshold(gray, 64, 255, cv.THRESH_BINARY_INV)
                            res = read_license_plate(thresh)
                            if res and res != -1: car_memory[car_id]['text'] = str(res[0])
                        except: pass

        # 6. DRAWING REDUCED LINES
        cv.line(frame, (L1_X_START, LINE_1_Y), (L1_X_END, LINE_1_Y), (255, 100, 0), 4)
        cv.line(frame, (L2_X_START, LINE_2_Y), (L2_X_END, LINE_2_Y), (0, 100, 255), 4)
        
        for car_id, data in car_memory.items():
            if frame_nmr - data.get('last_seen', 0) > 20: continue
            x1, y1, x2, y2 = map(int, data['box'])
            cap_s = data.get('captured_speed')
            color = (0, 0, 255) if cap_s else (0, 255, 0)
            txt = f"{data['type']}: {data['text']}" + (f" [{cap_s} km/h]" if cap_s else "")
            cv.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv.putText(frame, txt, (x1, y1 - 10), cv.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # 7. DRAW DASHBOARDS
        draw_lane_dashboard(frame, "LANE 1 (UPPER)", lane_stats['Lane 1'], 30, 30, (255, 100, 0))
        draw_lane_dashboard(frame, "LANE 2 (LOWER)", lane_stats['Lane 2'], 450, 30, (0, 100, 255))

        f_resized = cv.resize(frame, (1280, 720))
        _, buffer = cv.imencode('.jpg', f_resized)
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/')
def index():
    return '<body style="background:#111;text-align:center;"><img src="/video_feed" style="width:90%;"></body>'

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)

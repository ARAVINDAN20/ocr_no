import cv2 as cv
import numpy as np
from ultralytics import YOLO
from sort.sort import Sort
from utils import map_car, read_license_plate

def main():
    # Load models
    print("Loading models on GPU...")
    vehicle_model = YOLO('yolov8n.pt')
    vehicle_model.to('cuda')
    plate_model = YOLO('./models/license_plate_detector.pt')
    plate_model.to('cuda')
    
    # Initialize Tracker
    mot_tracker = Sort()
    
    # Vehicle classes (car, motorcycle, bus, truck)
    vehicle_classes = [2, 3, 5, 7]
    
    # Open Video
    video_path = './1.mp4'
    cap = cv.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error reading video file {video_path}")
        return

    # Video Writer
    width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv.CAP_PROP_FPS)
    fourcc = cv.VideoWriter_fourcc(*'mp4v')
    out = cv.VideoWriter('out.mp4', fourcc, fps, (width, height))
    
    print("Starting processing... Press 'q' to quit.")
    
    frame_nmr = -1
    ret = True
    
    while ret:
        frame_nmr += 1
        ret, frame = cap.read()
        if not ret:
            break
            
        # 1. Detect Vehicles
        vehicles = vehicle_model(frame, verbose=False)[0]
        detections_ = []
        for vehicle in vehicles.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = vehicle
            if int(class_id) in vehicle_classes:
                detections_.append([x1, y1, x2, y2, score])
        
        # 2. Track Vehicles
        track_ids = mot_tracker.update(np.asarray(detections_))
        
        # 3. Detect License Plates
        plates = plate_model(frame, verbose=False)[0]
        
        # Process each plate
        for plate in plates.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = plate
            
            # Map plate to vehicle
            x1car, y1car, x2car, y2car, car_id = map_car(plate, track_ids)
            
            if car_id != -1:
                # Crop and Read
                plate_crop = frame[int(y1):int(y2), int(x1):int(x2), :]
                
                # Preprocess for OCR (grayscale + threshold)
                plate_gray = cv.cvtColor(plate_crop, cv.COLOR_BGR2GRAY)
                _, plate_thresh = cv.threshold(plate_gray, 64, 255, cv.THRESH_BINARY_INV)
                
                # OCR
                result = read_license_plate(plate_thresh)
                if result is not None and result != -1:
                    license_text, license_score = result
                    
                    if license_text is not None and license_text != -1:
                        # Visualization (Draw on Frame)
                        # Draw Vehicle Box
                        cv.rectangle(frame, (int(x1car), int(y1car)), (int(x2car), int(y2car)), (0, 255, 0), 2)
                        
                        # Draw Plate Box
                        cv.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)
                        
                        # Draw Text
                        text_display = f"{license_text}"
                        (text_w, text_h), _ = cv.getTextSize(text_display, cv.FONT_HERSHEY_SIMPLEX, 1, 2)
                        cv.rectangle(frame, (int(x1car), int(y1car)-30), (int(x1car)+text_w, int(y1car)), (255, 255, 255), -1)
                        cv.putText(frame, text_display, (int(x1car), int(y1car)-5), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2)
                        
                        print(f"Frame {frame_nmr}: Car {int(car_id)} - {license_text}")

        # Show Real-time
        # Resize for display if too large (optional, but good for laptop screens)
        display_frame = cv.resize(frame, (1280, 720))
        cv.imshow('Real-time ANPR', display_frame)
        
        # Save Output
        out.write(frame)
        
        # if cv.waitKey(1) & 0xFF == ord('q'):
        #    break

    cap.release()
    out.release()
    cv.destroyAllWindows()
    print("Done. Saved to out.mp4")

if __name__ == '__main__':
    main()

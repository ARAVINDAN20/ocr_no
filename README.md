# ANPR Live Dashboard 🚗📊

A real-time **Automatic Number Plate Recognition (ANPR)** system with a beautiful live dashboard. This application detects vehicles, reads license plates, tracks speed, and monitors traffic across multiple lanes.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-brightgreen.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-red.svg)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-yellow.svg)

---

## ✨ Features

- **🎥 Live Video Processing** - Real-time vehicle detection from video streams
- **🔢 License Plate Recognition** - OCR-powered number plate reading using EasyOCR
- **⚡ Speed Detection** - Calculate vehicle speeds as they cross detection lines
- **🛣️ Multi-Lane Monitoring** - Track vehicles across Lane 1 and Lane 2
- **📊 Live Dashboard** - Beautiful animated web interface with real-time updates
- **📈 Graph Reports** - Visual analytics including:
  - Vehicle type distribution (pie chart)
  - Lane comparison (bar chart)
  - Speed histogram
  - Timeline view
- **🔍 Advanced Filtering** - Filter by vehicle type, lane, or search by plate number
- **💾 Data Export** - Download data in CSV or JSON format
- **🐳 Docker Ready** - Cross-platform deployment with a single command

---

## 🖥️ Dashboard Preview

The dashboard includes:
- Live video feed with detection overlays
- Real-time statistics cards (total vehicles, per-lane counts, average speed)
- Vehicle detection table with animated updates
- Interactive charts and graphs
- Filter controls and export options

---

## 🚀 Quick Start

### Option 1: Docker (Recommended) 🐳

The easiest way to run the application on **Windows**, **macOS**, or **Linux**.

#### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) installed on your system

#### Run with Docker Compose (Simplest)

```bash
# Clone the repository
git clone https://github.com/ARAVINDAN20/ocr_no.git
cd ocr_no

# Switch to test branch
git checkout test

# Build and run with a single command
docker-compose up --build
```

#### Run with Docker CLI

```bash
# Build the image
docker build -t anpr-dashboard .

# Run the container
docker run -p 5001:5001 anpr-dashboard
```

#### Access the Dashboard
Open your browser and navigate to:
```
http://localhost:5001
```

---

### Option 2: Local Installation 🐍

#### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- CUDA (optional, for GPU acceleration)

#### Installation Steps

```bash
# Clone the repository
git clone https://github.com/ARAVINDAN20/ocr_no.git
cd ocr_no

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python speed_lane_dashboard.py
```

---

## 📁 Project Structure

```
Video-ANPR/
├── speed_lane_dashboard.py   # Main application with Flask server
├── speed_lane.py             # Original detection script
├── utils.py                  # Utility functions for OCR
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker build configuration
├── docker-compose.yml        # Docker Compose configuration
├── 1.mp4                     # Input video file
├── models/
│   └── license_plate_detector.pt  # License plate detection model
├── sort/
│   └── sort.py               # SORT tracking algorithm
├── templates/
│   └── dashboard.html        # Dashboard HTML template
└── static/
    ├── css/
    │   └── dashboard.css     # Dashboard styles
    └── js/
        └── dashboard.js      # Dashboard JavaScript
```

---

## 🔧 Configuration

### Lane Detection Lines

Edit `speed_lane_dashboard.py` to adjust lane detection lines:

```python
# Lane 1 (Upper)
LINE_1_Y = 1100
L1_X_START, L1_X_END = 800, 1900

# Lane 2 (Lower)
LINE_2_Y = 1550
L2_X_START, L2_X_END = 1900, 3000
```

### Video Source

Change the video source in `speed_lane_dashboard.py`:

```python
video_path = './1.mp4'  # Change to your video file
```

### Port Configuration

Default port is `5001`. To change:

```python
# In speed_lane_dashboard.py
socketio.run(app, host='0.0.0.0', port=5001)  # Change port here
```

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard web interface |
| `/video_feed` | GET | Live video stream (MJPEG) |
| `/api/vehicles` | GET | Get all detected vehicles |
| `/api/stats` | GET | Get lane statistics |
| `/api/download/csv` | GET | Download data as CSV |
| `/api/download/json` | GET | Download data as JSON |
| `/api/clear` | GET | Clear all collected data |

---

## 🔌 WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `connect` | Server→Client | Initial connection, sends current data |
| `vehicle_crossed` | Server→Client | New vehicle detected crossing a lane |
| `plate_updated` | Server→Client | License plate OCR result updated |
| `data_cleared` | Server→Client | All data has been cleared |

---

## 📊 Data Export Format

### CSV Format
```csv
ID,Vehicle ID,Type,Number Plate,Speed (km/h),Lane,Timestamp
1,42,Car,ABC1234,65,Lane 1,2025-12-12T10:15:30
```

### JSON Format
```json
{
  "export_timestamp": "2025-12-12T10:15:30",
  "summary": {
    "total_vehicles": 25,
    "lane_1_total": 12,
    "lane_2_total": 13,
    "type_breakdown": {
      "Car": 15,
      "Bike": 5,
      "Bus": 3,
      "Truck": 2
    }
  },
  "lane_stats": { ... },
  "vehicles": [ ... ]
}
```

---

## 🖥️ System Requirements

### Minimum Requirements
- **CPU**: Intel Core i5 / AMD Ryzen 5 or equivalent
- **RAM**: 8 GB
- **Storage**: 2 GB free space
- **OS**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+)

### Recommended (for GPU acceleration)
- **GPU**: NVIDIA GPU with CUDA support
- **VRAM**: 4 GB+
- **CUDA**: 11.8 or higher

---

## 🐳 Docker Details

### Build Arguments

```bash
# Build with custom tag
docker build -t anpr-dashboard:v1.0 .

# Build for specific platform
docker build --platform linux/amd64 -t anpr-dashboard .
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PYTHONUNBUFFERED` | `1` | Force unbuffered output |

### GPU Support (NVIDIA)

To enable GPU support in Docker:

1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

2. Run with GPU:
```bash
docker run --gpus all -p 5001:5001 anpr-dashboard
```

Or uncomment GPU section in `docker-compose.yml`.

---

## 🛠️ Troubleshooting

### Common Issues

**1. Video not loading**
- Ensure `1.mp4` exists in the project directory
- Check video codec compatibility

**2. Port already in use**
```bash
# Use a different port
docker run -p 5002:5001 anpr-dashboard
```

**3. Out of memory**
- Reduce video resolution
- Use CPU mode if GPU memory is limited

**4. License plates not detected**
- Adjust detection confidence threshold
- Ensure good video quality

---

## 📝 License

This project is for educational purposes.

---

## 👥 Contributors

- ARAVINDAN20

---

## 📧 Support

For issues and feature requests, please open an issue on GitHub.

---

**Made with ❤️ for traffic monitoring and analysis**

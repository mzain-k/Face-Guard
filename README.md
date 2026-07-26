# FaceGuard
Real-time face recognition based physical security platform.
Deployable to any house, office, or space — one codebase, any location.

## How it works
1. Camera stream is sampled at 2-5fps
2. Faces are detected and tracked across frames
3. Liveness check rejects photos/screens (anti-spoof)
4. ArcFace embeddings matched against enrolled personnel
5. Temporal voter requires consistent match across 5 frames before decision fires
6. Authorized → bell rings. Unknown for 30s → WhatsApp alert sent to owner

## Stack
- Python 3.11
- insightface (ArcFace buffalo_s) — face detection + recognition
- MiniFASNetV2 ONNX — liveness/anti-spoof
- OpenCV — camera abstraction
- SQLite + SQLAlchemy — event logging
- FastAPI — dashboard backend
- React — dashboard frontend
- pyserial — USB relay bell control
- pywa — WhatsApp alerts (plug in credentials when ready)

## Requirements
- Python 3.11
- Webcam or IP camera (RTSP/MJPEG)
- Windows 10/11
- Optional: CH340 USB relay module for physical bell
- Optional: Meta WhatsApp Business account for alerts

## Setup

### 1. Create virtual environment
```bash
py -3.11 -m venv faceguard-env
faceguard-env\Scripts\activate
pip install -r requirements.txt
```

### 2. Config
```bash
cp config/deployment.yaml.example config/deployment.yaml
# Edit deployment.yaml with your camera source, phone number, and rules
```

### 3. Enroll personnel
```bash
python enrollment/enroll.py
```

### 4. Run the system
```bash
# Double-click run.bat
# or
python main.py
```

### 5. Run the dashboard
```bash
# Double-click run_dashboard.bat
# or open two terminals:
# Terminal 1: cd dashboard/backend && uvicorn main:app --port 8000
# Terminal 2: cd dashboard/frontend && npm start
# Open http://localhost:3000
```

## Camera config
```yaml
# Webcam
source: 0

# Phone (install IP Webcam app on Android)
source: "http://192.168.x.x:8080/video"

# Real CCTV (Hikvision/Dahua)
source: "rtsp://admin:password@192.168.x.x:554/stream"
```

## Hardware (optional)
- **Bell/buzzer**: CH340 USB relay module (~$3-5 on Daraz/AliExpress)
- Set `relay.enabled: true` and `relay.port: COM3` in deployment.yaml
- Connect bell to relay NO terminals

## WhatsApp alerts (optional)
- Create Meta Business account
- Register WhatsApp Business number
- Set `WHATSAPP_PHONE_ID` and `WHATSAPP_TOKEN` environment variables
- Set `self.enabled = True` in `alerts/whatsapp.py`

## Project structure
```
Face-Guard/
├── config/ # deployment config per install
├── core/ # detection, recognition, tracking, liveness, rules
├── alerts/ # WhatsApp + bell controllers
├── dashboard/ # FastAPI backend + React frontend
├── data/ # personnel DB, snapshots, event log
├── enrollment/ # face enrollment script
├── models/ # ONNX model files
└── main.py # entry point
```

## Built by
- Zain — BSCS @ NUST, Quetta
- github.com/mzain-k
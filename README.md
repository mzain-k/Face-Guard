# FaceGuard
Real-time face recognition based physical security platform.
Deployable to any house, office, or space.

## Stack
Python 3.11 · insightface · OpenCV · FastAPI · SQLite · pyserial

## Setup
```bash
py -3.11 -m venv faceguard-env
faceguard-env\Scripts\activate
pip install -r requirements.txt
```

## Config
Copy and edit the deployment config:
```bash
cp config/deployment.yaml.example config/deployment.yaml
```

## Run
```bash
python Face-Guard/main.py
```

## Project Status
🚧 Active development
import os
import sys
import json
import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime

from db import init_db, log_event, SessionLocal, Event
from core.recognizer import FaceRecognizer
from core.detector import FaceDetector

import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../../config/deployment.yaml")
with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)

PERSONNEL_DIR = os.path.join(os.path.dirname(__file__), "../../data/personnel")
SNAPSHOTS_DIR = os.path.join(os.path.dirname(__file__), "../../data/snapshots")

app = FastAPI(title="FaceGuard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

detector = FaceDetector(model_pack=config["recognition"]["model_pack"])
recognizer = FaceRecognizer(threshold=config["recognition"]["threshold"])


@app.on_event("startup")
def startup():
    init_db()
    detector.load()
    recognizer.load()


# --- Personnel ---

@app.get("/personnel")
def get_personnel():
    meta_path = os.path.join(PERSONNEL_DIR, "metadata.json")
    if not os.path.exists(meta_path):
        return []
    with open(meta_path) as f:
        return json.load(f)


@app.delete("/personnel/{name}")
def delete_person(name: str):
    import numpy as np
    meta_path = os.path.join(PERSONNEL_DIR, "metadata.json")
    emb_path  = os.path.join(PERSONNEL_DIR, "embeddings.npy")

    with open(meta_path) as f:
        metadata = json.load(f)

    names = [m["name"] for m in metadata]
    if name not in names:
        return JSONResponse(status_code=404, content={"error": "Person not found"})

    idx = names.index(name)
    metadata.pop(idx)
    embeddings = np.load(emb_path)
    embeddings = np.delete(embeddings, idx, axis=0)

    np.save(emb_path, embeddings)
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    recognizer.reload()
    return {"message": f"{name} removed"}


# --- Events ---

@app.get("/events")
def get_events(limit: int = 50):
    db = SessionLocal()
    try:
        events = db.query(Event).order_by(Event.timestamp.desc()).limit(limit).all()
        return [
            {
                "id": e.id,
                "timestamp": e.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "camera_id": e.camera_id,
                "name": e.name,
                "access": e.access,
                "confidence": e.confidence,
                "action": e.action,
                "snapshot": f"/snapshots/{os.path.basename(e.snapshot_path)}"
                            if e.snapshot_path else None
            }
            for e in events
        ]
    finally:
        db.close()


# --- Snapshots ---

@app.get("/snapshots/{filename}")
def get_snapshot(filename: str):
    path = os.path.join(SNAPSHOTS_DIR, filename)
    if not os.path.exists(path):
        return JSONResponse(status_code=404, content={"error": "Not found"})
    return FileResponse(path)


# --- Status ---

@app.get("/status")
def status():
    return {
        "deployment": config["deployment"]["name"],
        "personnel_count": len(get_personnel()),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
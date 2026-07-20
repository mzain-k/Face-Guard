import cv2
import yaml
import logging
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.camera import CameraManager
from core.detector import FaceDetector
from core.recognizer import FaceRecognizer
from core.voter import TemporalVoter

logging.basicConfig(level=logging.INFO)

with open("Face-Guard/config/deployment.yaml") as f:
    config = yaml.safe_load(f)

# Load all components
detector = FaceDetector(model_pack=config["recognition"]["model_pack"])
detector.load()

recognizer = FaceRecognizer(threshold=config["recognition"]["threshold"])
recognizer.load()

voter = TemporalVoter(
    vote_frames=config["recognition"]["vote_frames"],
    vote_window_sec=config["recognition"]["vote_window_sec"]
)

manager = CameraManager(config["cameras"])
manager.start_all()
time.sleep(2)

# Color map
ACCESS_COLORS = {
    "authorized": (0, 255, 0),    # green
    "blocked":    (0, 0, 255),    # red
    "denied":     (0, 165, 255),  # orange — unknown person
}

print("\nRecognizer running — press Q to quit\n")

# Simple track ID per frame (no ByteTrack yet — added next session)
track_counter = 0

while True:
    frames = manager.read_all()

    if not frames:
        cv2.waitKey(1)
        continue

    for cam_id, frame in frames.items():
        faces = detector.detect(frame)

        for face in faces:
            embedding = face.embedding
            if embedding is None:
                continue

            # Match against personnel DB
            result = recognizer.match(embedding)

            # Vote for temporal consistency
            track_id = f"{cam_id}_face_{track_counter}"
            decision = voter.vote(track_id, result)

            # Draw bounding box
            x1, y1, x2, y2 = [int(v) for v in face.bbox]
            color = ACCESS_COLORS.get(result["access"], (255, 255, 255))

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Label — show live result even before voter decides
            label = f"{result['name']} ({result['confidence']:.2f})"
            cv2.putText(
                frame, label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7, color, 2
            )

            # Show voter decision as overlay when it fires
            if decision:
                status = f">> {decision['name']} — {decision['access'].upper()}"
                cv2.putText(
                    frame, status,
                    (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, color, 2
                )
                print(status)

        cv2.putText(
            frame,
            f"Faces: {len(faces)}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8, (255, 255, 255), 2
        )

        cv2.imshow(f"FaceGuard | {cam_id}", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Stopping...")
        break

manager.stop_all()
cv2.destroyAllWindows()
print("Done.")
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
from core.tracker import FaceTracker
from core.rules import RulesEngine

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

tracker = FaceTracker()
rules = RulesEngine(config)

manager = CameraManager(config["cameras"])
manager.start_all()
time.sleep(2)

ACCESS_COLORS = {
    "authorized": (0, 255, 0),
    "blocked":    (0, 0, 255),
    "denied":     (0, 165, 255),
}

print("\nFaceGuard running — press Q to quit\n")

while True:
    frames = manager.read_all()

    if not frames:
        cv2.waitKey(1)
        continue

    for cam_id, frame in frames.items():
        faces = detector.detect(frame)
        tracked = tracker.update(faces)

        for track_id, face in tracked:
            embedding = face.embedding
            if embedding is None:
                continue

            result = recognizer.match(embedding)
            tid_str = f"{cam_id}_{track_id}"
            decision = voter.vote(tid_str, result)

            # Draw live bbox
            x1, y1, x2, y2 = [int(v) for v in face.bbox]
            color = ACCESS_COLORS.get(result["access"], (255, 255, 255))
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            label = f"[{track_id}] {result['name']} ({result['confidence']:.2f})"
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)

            # Process voter decision through rules engine
            if decision:
                action = rules.evaluate(tid_str, decision)

                status = f">> {decision['name']} - {decision['access'].upper()}"
                cv2.putText(frame, status, (10, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)

                print(f"[{cam_id}] {status} | Bell: {action['ring_bell']} "
                      f"| Alert: {action['send_alert']} | {action['reason']}")

        cv2.putText(frame, f"Faces: {len(faces)}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        cv2.imshow(f"FaceGuard | {cam_id}", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Stopping...")
        break

manager.stop_all()
cv2.destroyAllWindows()
print("Done.")
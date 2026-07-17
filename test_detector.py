import cv2
import yaml
import logging
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.camera import CameraManager
from core.detector import FaceDetector

logging.basicConfig(level=logging.INFO)

with open("Face-Guard/config/deployment.yaml") as f:
    config = yaml.safe_load(f)

# Load detector first — may download model
detector = FaceDetector(
    model_pack=config["recognition"]["model_pack"]
)
detector.load()

# Start cameras
manager = CameraManager(config["cameras"])
manager.start_all()
time.sleep(2)

print("\nDetector running — press Q to quit\n")

while True:
    frames = manager.read_all()

    if not frames:
        cv2.waitKey(1)
        continue

    for cam_id, frame in frames.items():
        faces = detector.detect(frame)

        # Draw detections
        frame = detector.draw(frame, faces)

        # Show face count
        cv2.putText(
            frame,
            f"Faces detected: {len(faces)}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1, (0, 255, 0), 2
        )

        cv2.imshow(f"FaceGuard | {cam_id}", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        print("Stopping...")
        break

manager.stop_all()
cv2.destroyAllWindows()
print("Done.")
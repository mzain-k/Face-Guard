import cv2
import yaml
import logging
import sys
import os

# So Python finds core/ as a module regardless of where you run from
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.camera import CameraManager

logging.basicConfig(level=logging.INFO)

with open("Face-Guard/config/deployment.yaml") as f:
    config = yaml.safe_load(f)

manager = CameraManager(config["cameras"])
manager.start_all()

print("\nCamera status:", manager.status())
print("Feed running — press Q to quit\n")

while True:
    frames = manager.read_all()

    for cam_id, frame in frames.items():
        # Overlay camera ID on frame
        cv2.putText(
            frame,
            f"Camera: {cam_id}",
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
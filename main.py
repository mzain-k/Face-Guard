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
from alerts.whatsapp import WhatsAppAlerter
from alerts.bell import BellController

# Suppress OpenVINO DLL warning — falls back to CPU cleanly
os.environ["ORT_LOGGING_LEVEL"] = "3"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("faceguard.main")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config/deployment.yaml")


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def main():
    config = load_config()

    logger.info(f"Starting FaceGuard — {config['deployment']['name']}")

    # Initialize all components
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

    alerter = WhatsAppAlerter(
        owner_phone=config["deployment"]["owner_phone"]
    )

    relay_cfg = config.get("relay", {})
    bell = BellController(
        enabled=relay_cfg.get("enabled", False),
        port=relay_cfg.get("port", "COM3"),
        baud=relay_cfg.get("baud", 9600),
        ring_duration_sec=relay_cfg.get("ring_duration_sec", 2)
    )

    manager = CameraManager(config["cameras"])
    manager.start_all()
    time.sleep(2)

    logger.info("Pipeline running. Press Q to quit.")

    ACCESS_COLORS = {
        "authorized": (0, 255, 0),
        "blocked":    (0, 0, 255),
        "denied":     (0, 165, 255),
    }

    try:
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

                    label = f"{result['name']} ({result['confidence']:.2f})"
                    cv2.putText(frame, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)

                    # Process voter decision
                    if decision:
                        action = rules.evaluate(tid_str, decision)

                        status = f"{decision['name']} - {decision['access'].upper()}"
                        cv2.putText(frame, f">> {status}", (10, 70),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)

                        logger.info(
                            f"[{cam_id}] {status} | "
                            f"Bell: {action['ring_bell']} | "
                            f"Alert: {action['send_alert']}"
                        )

                        # Trigger bell
                        if action["ring_bell"]:
                            bell.ring()

                        # Send alert
                        if action["send_alert"]:
                            alerter.send_alert(
                                reason=action["reason"],
                                camera_id=cam_id,
                                frame=frame
                            )

                cv2.putText(frame, f"Faces: {len(faces)}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

                cv2.putText(frame,
                            config["deployment"]["name"],
                            (10, frame.shape[0] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

                cv2.imshow(f"FaceGuard | {cam_id}", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        logger.info("Interrupted by user.")

    finally:
        logger.info("Shutting down...")
        manager.stop_all()
        bell.close()
        cv2.destroyAllWindows()
        logger.info("FaceGuard stopped.")


if __name__ == "__main__":
    main()
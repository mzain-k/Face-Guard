import cv2
import numpy as np
import json
import os
import sys
import time
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.detector import FaceDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PERSONNEL_DIR = os.path.join(os.path.dirname(__file__), "../data/personnel")
EMBEDDINGS_FILE = os.path.join(PERSONNEL_DIR, "embeddings.npy")
METADATA_FILE = os.path.join(PERSONNEL_DIR, "metadata.json")

SAMPLES_NEEDED = 20  # frames to capture per person


def load_existing():
    """Load existing embeddings and metadata if they exist."""
    if os.path.exists(EMBEDDINGS_FILE) and os.path.exists(METADATA_FILE):
        embeddings = np.load(EMBEDDINGS_FILE)
        with open(METADATA_FILE, "r") as f:
            metadata = json.load(f)
        logger.info(f"Loaded {len(metadata)} existing personnel records.")
        return embeddings, metadata
    return np.empty((0, 512), dtype=np.float32), []


def save(embeddings: np.ndarray, metadata: list):
    """Save embeddings and metadata to disk."""
    os.makedirs(PERSONNEL_DIR, exist_ok=True)
    np.save(EMBEDDINGS_FILE, embeddings)
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved {len(metadata)} personnel records.")


def enroll():
    # Get person info
    name = input("Enter person's name: ").strip()
    role = input("Enter role (e.g. owner, family, staff): ").strip()
    access = input("Access level (authorized / blocked): ").strip().lower()

    if access not in ("authorized", "blocked"):
        print("Invalid access level. Use 'authorized' or 'blocked'.")
        return

    # Load detector
    detector = FaceDetector(model_pack="buffalo_s")
    detector.load()

    # Open webcam
    cap = cv2.VideoCapture(0)
    time.sleep(1.0)

    if not cap.isOpened():
        logger.error("Cannot open webcam.")
        return

    print(f"\nEnrolling: {name}")
    print(f"Look at the camera. Collecting {SAMPLES_NEEDED} samples...")
    print("Press Q to cancel.\n")

    samples = []

    while len(samples) < SAMPLES_NEEDED:
        ret, frame = cap.read()
        if not ret:
            continue

        faces = detector.detect(frame)
        display = frame.copy()

        if len(faces) == 1:
            face = faces[0]
            embedding = face.embedding

            if embedding is not None:
                # Normalize embedding
                embedding = embedding / np.linalg.norm(embedding)
                samples.append(embedding)

                # Draw progress
                x1, y1, x2, y2 = [int(v) for v in face.bbox]
                cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    display,
                    f"Capturing: {len(samples)}/{SAMPLES_NEEDED}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 255, 0), 2
                )
        elif len(faces) == 0:
            cv2.putText(
                display,
                "No face detected — move closer",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0, 0, 255), 2
            )
        else:
            cv2.putText(
                display,
                "Multiple faces — ensure only one person is visible",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (0, 165, 255), 2
            )

        cv2.imshow("FaceGuard Enrollment", display)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Enrollment cancelled.")
            cap.release()
            cv2.destroyAllWindows()
            return

    cap.release()
    cv2.destroyAllWindows()

    # Average all samples into one stable embedding
    final_embedding = np.mean(samples, axis=0)
    final_embedding = final_embedding / np.linalg.norm(final_embedding)

    # Load existing and append
    embeddings, metadata = load_existing()

    # Check if person already exists — update instead of duplicate
    existing_names = [m["name"] for m in metadata]
    if name in existing_names:
        idx = existing_names.index(name)
        embeddings[idx] = final_embedding
        metadata[idx] = {"name": name, "role": role, "access": access}
        print(f"\nUpdated existing record for: {name}")
    else:
        embeddings = np.vstack([embeddings, final_embedding])
        metadata.append({"name": name, "role": role, "access": access})
        print(f"\nNew record created for: {name}")

    save(embeddings, metadata)
    print(f"Enrollment complete. Total personnel: {len(metadata)}")


if __name__ == "__main__":
    enroll()
import numpy as np
import json
import os
import logging

logger = logging.getLogger(__name__)

PERSONNEL_DIR = os.path.join(os.path.dirname(__file__), "../data/personnel")
EMBEDDINGS_FILE = os.path.join(PERSONNEL_DIR, "embeddings.npy")
METADATA_FILE = os.path.join(PERSONNEL_DIR, "metadata.json")


class FaceRecognizer:
    """
    Matches a detected face's embedding against
    the enrolled personnel database using cosine similarity.
    """

    def __init__(self, threshold: float = 0.45):
        self.threshold = threshold
        self.embeddings = None
        self.metadata = []

    def load(self):
        """Load personnel DB from disk. Call once at startup."""
        if not os.path.exists(EMBEDDINGS_FILE) or not os.path.exists(METADATA_FILE):
            logger.warning(
                "No personnel database found. "
                "Run enrollment/enroll.py to enroll people first."
            )
            return

        self.embeddings = np.load(EMBEDDINGS_FILE)
        with open(METADATA_FILE, "r") as f:
            self.metadata = json.load(f)

        logger.info(f"Loaded {len(self.metadata)} personnel records.")

    def reload(self):
        """Hot-reload DB without restarting — useful after new enrollment."""
        self.load()

    def match(self, embedding: np.ndarray) -> dict:
        """
        Compare a face embedding against all enrolled personnel.

        Returns:
          {
            "name": "Zain",
            "role": "owner",
            "access": "authorized",
            "confidence": 0.91,
            "matched": True
          }
          or if no match:
          {
            "name": "Unknown",
            "role": None,
            "access": "denied",
            "confidence": 0.0,
            "matched": False
          }
        """
        if self.embeddings is None or len(self.metadata) == 0:
            return self._unknown(0.0)

        # Normalize incoming embedding
        embedding = embedding / np.linalg.norm(embedding)

        # Cosine similarity against all enrolled embeddings
        similarities = np.dot(self.embeddings, embedding)
        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])

        if best_score >= self.threshold:
            person = self.metadata[best_idx]
            return {
                "name": person["name"],
                "role": person["role"],
                "access": person["access"],
                "confidence": round(best_score, 4),
                "matched": True
            }

        return self._unknown(best_score)

    def _unknown(self, confidence: float) -> dict:
        return {
            "name": "Unknown",
            "role": None,
            "access": "denied",
            "confidence": round(confidence, 4),
            "matched": False
        }
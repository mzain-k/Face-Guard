import numpy as np
import logging
from insightface.app import FaceAnalysis

logger = logging.getLogger(__name__)


class FaceDetector:
    """
    Wraps insightface FaceAnalysis for face detection.
    Returns detected faces with bounding boxes,
    landmarks, and embeddings from each frame.
    """

    def __init__(self, model_pack: str = "buffalo_s", det_size: tuple = (320, 320)):
        self.model_pack = model_pack
        self.det_size = det_size
        self.app = None

    def load(self):
        """
        Downloads model on first run (~150MB for buffalo_s).
        Subsequent runs load from cache at ~/.insightface/models/
        Call this once at startup — not per frame.
        """
        logger.info(f"Loading face detection model: {self.model_pack}")
        logger.info("First run will download the model — this may take a minute...")

        self.app = FaceAnalysis(
            name=self.model_pack,
            providers=["OpenVINOExecutionProvider", "CPUExecutionProvider"]
        )
        self.app.prepare(ctx_id=0, det_size=self.det_size)
        logger.info("Model loaded and ready.")

    def detect(self, frame: np.ndarray) -> list:
        """
        Runs detection on a single frame.
        Returns list of face objects, each with:
          - face.bbox         -> [x1, y1, x2, y2]
          - face.embedding    -> 512-dim ArcFace vector
          - face.det_score    -> detection confidence 0-1
          - face.landmark_2d_106 -> facial landmarks

        Returns empty list if no faces found.
        """
        if self.app is None:
            raise RuntimeError("FaceDetector not loaded. Call load() first.")

        if frame is None or frame.size == 0:
            return []

        try:
            faces = self.app.get(frame)
            # Filter out very low confidence detections
            faces = [f for f in faces if f.det_score > 0.5]
            return faces
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return []

    def draw(self, frame: np.ndarray, faces: list) -> np.ndarray:
        """
        Draws bounding boxes and scores on frame.
        Used for testing — not used in production pipeline.
        """
        import cv2
        for face in faces:
            x1, y1, x2, y2 = [int(v) for v in face.bbox]
            score = face.det_score

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame,
                f"{score:.2f}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (0, 255, 0), 2
            )
        return frame
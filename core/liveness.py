import cv2
import numpy as np
import onnxruntime as ort
import os
import logging

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../models/MiniFASNetV2.onnx")

# MiniFASNetV2 constants
INPUT_SIZE = (80, 80)
SCALE     = 2.7
MEAN      = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD       = np.array([0.229, 0.224, 0.225], dtype=np.float32)


class LivenessDetector:
    """
    Anti-spoofing using MiniFASNetV2 ONNX model.
    Detects if a face is real (live) or fake (photo/screen/mask).

    No PyTorch required — pure ONNX Runtime inference.
    Model: ~1.7MB, runs fast on CPU.
    """

    def __init__(self, spoof_threshold: float = 0.6):
        self.spoof_threshold = spoof_threshold
        self.session = None

    def load(self):
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Liveness model not found at {MODEL_PATH}\n"
                f"Download it with:\n"
                f"curl -L -o Face-Guard/models/MiniFASNetV2.onnx "
                f"https://github.com/yakhyo/face-anti-spoofing/releases/download/weights/MiniFASNetV2.onnx"
            )

        self.session = ort.InferenceSession(
            MODEL_PATH,
            providers=["CPUExecutionProvider"]
        )
        logger.info("Liveness model loaded.")

    def is_live(self, frame: np.ndarray, bbox: list) -> tuple[bool, float]:
        """
        Check if the face in bbox is a real live face.

        Args:
            frame: full BGR frame from camera
            bbox:  [x1, y1, x2, y2] face bounding box

        Returns:
            (is_live: bool, confidence: float)
            confidence = probability of being a real face (0.0 to 1.0)
        """
        if self.session is None:
            logger.warning("Liveness model not loaded — skipping check.")
            return True, 1.0

        face_crop = self._crop_face(frame, bbox)
        if face_crop is None:
            return True, 1.0

        tensor = self._preprocess(face_crop)

        input_name = self.session.get_inputs()[0].name
        outputs = self.session.run(None, {input_name: tensor})
        scores = outputs[0][0]  # [fake_score, real_score]

        # Softmax
        exp_scores = np.exp(scores - np.max(scores))
        probs = exp_scores / exp_scores.sum()

        real_prob = float(probs[1])
        live = real_prob >= self.spoof_threshold

        return live, real_prob

    def _crop_face(self, frame: np.ndarray, bbox: list):
        """Crop face with margin scaled by SCALE factor."""
        x1, y1, x2, y2 = [int(v) for v in bbox]
        w = x2 - x1
        h = y2 - y1

        # Add margin
        cx, cy = x1 + w // 2, y1 + h // 2
        new_size = int(max(w, h) * SCALE / 2)

        x1c = max(0, cx - new_size)
        y1c = max(0, cy - new_size)
        x2c = min(frame.shape[1], cx + new_size)
        y2c = min(frame.shape[0], cy + new_size)

        crop = frame[y1c:y2c, x1c:x2c]
        if crop.size == 0:
            return None
        return crop

    def _preprocess(self, face: np.ndarray) -> np.ndarray:
        """Resize, normalize, convert to NCHW tensor."""
        face = cv2.resize(face, INPUT_SIZE)
        face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
        face = face.astype(np.float32) / 255.0
        face = (face - MEAN) / STD
        face = face.transpose(2, 0, 1)       # HWC -> CHW
        face = np.expand_dims(face, axis=0)  # CHW -> NCHW
        return face
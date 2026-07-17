import cv2
import time
import threading
import logging

logger = logging.getLogger(__name__)


class CameraStream:
    """
    Unified camera abstraction.
    source=0          -> default webcam
    source="rtsp://..." -> IP cam or phone via RTSP
    source="http://192.168.x.x:8080/video" -> phone MJPEG stream

    Runs capture on a background thread so frame reads
    are never blocking. Pipeline always gets latest frame.
    """

    def __init__(self, camera_id: str, source, fps_sample: int = 3):
        self.camera_id = camera_id
        self.source = source
        self.fps_sample = fps_sample
        self.interval = 1.0 / fps_sample

        self._cap = None
        self._frame = None
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self._last_read_time = 0

    def start(self):
        self._cap = cv2.VideoCapture(self.source)

        # Give RTSP streams time to negotiate
        time.sleep(1.0)

        if not self._cap.isOpened():
            raise RuntimeError(
                f"[{self.camera_id}] Cannot open source: {self.source}\n"
                f"  - For webcam: check source is 0 (or 1 for external)\n"
                f"  - For phone: ensure IP Webcam app is running and URL is correct"
            )

        self._running = True
        self._thread = threading.Thread(
            target=self._capture_loop,
            daemon=True,
            name=f"cam-{self.camera_id}"
        )
        self._thread.start()
        logger.info(f"[{self.camera_id}] Started — source: {self.source}")

    def _capture_loop(self):
        """
        Continuously grabs latest frame from camera buffer.
        grab() flushes stale frames, retrieve() only when
        pipeline is ready — avoids processing old frames.
        """
        consecutive_failures = 0
        max_failures = 10

        while self._running:
            ret = self._cap.grab()

            if not ret:
                consecutive_failures += 1
                logger.warning(
                    f"[{self.camera_id}] Frame grab failed "
                    f"({consecutive_failures}/{max_failures})"
                )
                if consecutive_failures >= max_failures:
                    logger.error(
                        f"[{self.camera_id}] Too many failures — "
                        f"camera likely disconnected."
                    )
                    self._running = False
                    break
                time.sleep(0.5)
                continue

            consecutive_failures = 0  # reset on success

            now = time.time()
            if now - self._last_read_time >= self.interval:
                ret, frame = self._cap.retrieve()
                if ret:
                    with self._lock:
                        self._frame = frame
                    self._last_read_time = now

    def read(self):
        """
        Returns (True, frame) if a frame is available.
        Returns (False, None) if not ready yet.
        Non-blocking.
        """
        with self._lock:
            if self._frame is None:
                return False, None
            return True, self._frame.copy()

    def is_running(self):
        return self._running

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3.0)
        if self._cap:
            self._cap.release()
        logger.info(f"[{self.camera_id}] Stopped.")


class CameraManager:
    """
    Manages all camera streams from deployment.yaml config.
    One bad camera never crashes the whole system.
    """

    def __init__(self, camera_configs: list):
        self.cameras: dict[str, CameraStream] = {}
        for cfg in camera_configs:
            cam = CameraStream(
                camera_id=cfg["id"],
                source=cfg["source"],
                fps_sample=cfg.get("fps_sample", 3)
            )
            self.cameras[cfg["id"]] = cam

    def start_all(self):
        for cam in self.cameras.values():
            try:
                cam.start()
            except RuntimeError as e:
                logger.error(f"Failed to start camera: {e}")

    def read_all(self) -> dict:
        """Returns {camera_id: frame} for cameras that have a frame ready."""
        frames = {}
        for cam_id, cam in self.cameras.items():
            if not cam.is_running():
                continue
            ret, frame = cam.read()
            if ret:
                frames[cam_id] = frame
        return frames

    def stop_all(self):
        for cam in self.cameras.values():
            cam.stop()

    def status(self) -> dict:
        """Returns running status of each camera — useful for dashboard later."""
        return {
            cam_id: cam.is_running()
            for cam_id, cam in self.cameras.items()
        }
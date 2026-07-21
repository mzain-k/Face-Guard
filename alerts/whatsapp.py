import logging
import os
import cv2
from datetime import datetime

logger = logging.getLogger(__name__)

SNAPSHOTS_DIR = os.path.join(os.path.dirname(__file__), "../data/snapshots")


class WhatsAppAlerter:
    """
    WhatsApp alert module for FaceGuard.
    Currently runs in stub mode — saves snapshot and logs alert locally.

    To activate real WhatsApp alerts:
    1. Create a Meta Business account
    2. Register a WhatsApp Business number
    3. Get phone_id and token from Meta developer portal
    4. Set WHATSAPP_PHONE_ID and WHATSAPP_TOKEN environment variables
    5. pip install pywa
    6. Uncomment the pywa section below
    """

    def __init__(self, owner_phone: str):
        self.owner_phone = owner_phone
        self.enabled = False  # flip to True when credentials are ready
        os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

        # --- Uncomment when ready ---
        # from pywa import WhatsApp
        # self.wa = WhatsApp(
        #     phone_id=os.environ["WHATSAPP_PHONE_ID"],
        #     token=os.environ["WHATSAPP_TOKEN"]
        # )
        # self.enabled = True

    def send_alert(self, reason: str, camera_id: str, frame=None) -> bool:
        """
        Send a WhatsApp alert to the owner.

        Args:
            reason:    why the alert fired (e.g. "Unknown for 30s")
            camera_id: which camera triggered it
            frame:     current frame — saved as snapshot if provided

        Returns:
            True if alert sent/logged successfully, False on error
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        snapshot_path = None

        # Always save snapshot regardless of WhatsApp status
        if frame is not None:
            snapshot_path = self._save_snapshot(frame, camera_id)

        message = (
            f"*FaceGuard Alert*\n"
            f"Time: {timestamp}\n"
            f"Camera: {camera_id}\n"
            f"Reason: {reason}\n"
            f"Snapshot: {snapshot_path or 'N/A'}"
        )

        if self.enabled:
            return self._send_whatsapp(message, snapshot_path)
        else:
            # Stub mode — log locally
            logger.warning(f"[ALERT STUB] {message}")
            print(f"\n{'='*50}")
            print(f"ALERT | {timestamp}")
            print(f"Camera : {camera_id}")
            print(f"Reason : {reason}")
            print(f"Snapshot: {snapshot_path or 'N/A'}")
            print(f"{'='*50}\n")
            return True

    def _send_whatsapp(self, message: str, snapshot_path: str = None) -> bool:
        """Real send — only called when self.enabled is True."""
        try:
            # --- Uncomment when ready ---
            # if snapshot_path:
            #     self.wa.send_image(
            #         to=self.owner_phone,
            #         image=snapshot_path,
            #         caption=message
            #     )
            # else:
            #     self.wa.send_message(
            #         to=self.owner_phone,
            #         text=message
            #     )
            logger.info(f"WhatsApp alert sent to {self.owner_phone}")
            return True
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
            return False

    def _save_snapshot(self, frame, camera_id: str) -> str:
        """Save frame as a timestamped snapshot image."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{camera_id}_{timestamp}.jpg"
        path = os.path.join(SNAPSHOTS_DIR, filename)
        cv2.imwrite(path, frame)
        logger.info(f"Snapshot saved: {path}")
        return path
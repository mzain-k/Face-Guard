import logging
import time
import threading

logger = logging.getLogger(__name__)


class BellController:
    """
    USB relay controller for physical bell/buzzer.
    Uses pyserial to send open/close signals to a
    CH340-based USB relay module.

    Hardware setup:
    - CH340 USB relay module (~$3-5, available on Daraz/AliExpress)
    - Connect bell/buzzer to relay NO (Normally Open) terminals
    - Plug USB into laptop
    - Check COM port in Device Manager -> Ports

    Stub mode active until relay hardware is connected.
    To activate:
    1. Connect USB relay module
    2. Check COM port in Device Manager
    3. Update relay.port in deployment.yaml
    4. Set relay.enabled: true in deployment.yaml
    """

    # Standard CH340 relay command bytes
    RELAY_ON  = bytes([0xA0, 0x01, 0x01, 0xA2])
    RELAY_OFF = bytes([0xA0, 0x01, 0x00, 0xA1])

    def __init__(self, enabled: bool, port: str, baud: int, ring_duration_sec: float):
        self.enabled = enabled
        self.port = port
        self.baud = baud
        self.ring_duration_sec = ring_duration_sec
        self._serial = None
        self._lock = threading.Lock()

        if self.enabled:
            self._connect()

    def _connect(self):
        """Open serial connection to relay module."""
        try:
            import serial
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=1
            )
            logger.info(f"Bell relay connected on {self.port} at {self.baud} baud.")
        except Exception as e:
            logger.error(
                f"Bell relay connection failed on {self.port}: {e}\n"
                f"  - Check COM port in Device Manager\n"
                f"  - Ensure CH340 driver is installed\n"
                f"  - Falling back to stub mode"
            )
            self.enabled = False

    def ring(self):
        """
        Trigger the bell for ring_duration_sec.
        Non-blocking — runs on a background thread.
        """
        thread = threading.Thread(
            target=self._ring_blocking,
            daemon=True,
            name="bell-ring"
        )
        thread.start()

    def _ring_blocking(self):
        """Actual relay open/close — runs in background thread."""
        with self._lock:
            if self.enabled and self._serial:
                try:
                    self._serial.write(self.RELAY_ON)
                    logger.info(f"Bell ON — ringing for {self.ring_duration_sec}s")
                    time.sleep(self.ring_duration_sec)
                    self._serial.write(self.RELAY_OFF)
                    logger.info("Bell OFF")
                except Exception as e:
                    logger.error(f"Bell ring failed: {e}")
            else:
                # Stub mode
                logger.info(f"[BELL STUB] Ring for {self.ring_duration_sec}s")
                print(f"\n*** BELL RING — {self.ring_duration_sec}s ***\n")
                time.sleep(self.ring_duration_sec)

    def close(self):
        """Close serial connection on shutdown."""
        if self._serial and self._serial.is_open:
            self._serial.write(self.RELAY_OFF)
            self._serial.close()
            logger.info("Bell relay connection closed.")
            
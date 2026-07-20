import time
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class RulesEngine:
    """
    Evaluates access decisions and manages alert timing.
    Reads rules from deployment.yaml config.

    Responsibilities:
    - Track how long an unrecognized face has been present
    - Decide when to trigger bell vs alert
    - Prevent duplicate alerts for the same person
    """

    def __init__(self, config: dict):
        access_cfg = config.get("access", {})
        self.unrecognized_alert_sec = access_cfg.get("unrecognized_alert_sec", 30)
        self.bell_trigger_on = access_cfg.get("bell_trigger_on", "authorized")

        # track_id -> first_seen timestamp for unknowns
        self._unknown_since: dict[str, float] = {}

        # track_id -> last alert sent timestamp (avoid repeat alerts)
        self._last_alert: dict[str, float] = {}

        # track_id -> whether bell already triggered this appearance
        self._bell_triggered: set = set()

        # Cooldown between repeated alerts for same track (seconds)
        self.alert_cooldown_sec = 60.0

    def evaluate(self, track_id: str, decision: dict) -> dict:
        """
        Evaluate a voter decision and return an action dict.

        Returns:
        {
            "ring_bell": True/False,
            "send_alert": True/False,
            "action": "grant" | "deny" | "alert",
            "reason": str
        }
        """
        now = time.time()
        name = decision["name"]
        access = decision["access"]

        # Clear unknown timer if person is now recognized
        if decision["matched"]:
            self._unknown_since.pop(track_id, None)

        # --- Authorized person ---
        if access == "authorized":
            ring_bell = (
                self.bell_trigger_on == "authorized"
                and track_id not in self._bell_triggered
            )
            if ring_bell:
                self._bell_triggered.add(track_id)

            return {
                "ring_bell": ring_bell,
                "send_alert": False,
                "action": "grant",
                "reason": f"{name} authorized"
            }

        # --- Blocklisted person ---
        if access == "blocked":
            ring_bell = self.bell_trigger_on == "unauthorized"
            should_alert = self._should_alert(track_id, now)

            return {
                "ring_bell": ring_bell,
                "send_alert": should_alert,
                "action": "deny",
                "reason": f"{name} is blocklisted"
            }

        # --- Unknown person ---
        if track_id not in self._unknown_since:
            self._unknown_since[track_id] = now
            logger.info(f"Unknown face on track {track_id} — timer started.")

        elapsed = now - self._unknown_since[track_id]
        should_alert = (
            elapsed >= self.unrecognized_alert_sec
            and self._should_alert(track_id, now)
        )

        ring_bell = (
            self.bell_trigger_on == "unauthorized"
            and track_id not in self._bell_triggered
            and elapsed >= self.unrecognized_alert_sec
        )
        if ring_bell:
            self._bell_triggered.add(track_id)

        return {
            "ring_bell": ring_bell,
            "send_alert": should_alert,
            "action": "alert",
            "reason": f"Unknown for {elapsed:.0f}s"
        }

    def _should_alert(self, track_id: str, now: float) -> bool:
        """Respect cooldown — don't spam alerts for same person."""
        last = self._last_alert.get(track_id, 0)
        if now - last >= self.alert_cooldown_sec:
            self._last_alert[track_id] = now
            return True
        return False

    def clear_track(self, track_id: str):
        """Call when a track expires — clean up state."""
        self._unknown_since.pop(track_id, None)
        self._last_alert.pop(track_id, None)
        self._bell_triggered.discard(track_id)

    def clear_all(self):
        self._unknown_since.clear()
        self._last_alert.clear()
        self._bell_triggered.clear()
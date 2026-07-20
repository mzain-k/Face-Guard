import time
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class TemporalVoter:
    """
    Prevents single-frame false accepts/rejects by requiring
    a consistent match across multiple frames within a time window.

    A decision only fires when the same identity is matched
    vote_frames times within vote_window_sec seconds.
    """

    def __init__(self, vote_frames: int = 5, vote_window_sec: float = 2.0):
        self.vote_frames = vote_frames
        self.vote_window_sec = vote_window_sec

        # track_id -> list of (timestamp, match_result)
        self._votes: dict[str, list] = defaultdict(list)

    def vote(self, track_id: str, match_result: dict) -> dict | None:
        """
        Submit a match result for a tracked face.

        Returns a final decision dict if consensus is reached, else None.
        Decision dict is the match_result with an added "decided" key.

        Call this every frame per tracked face.
        """
        now = time.time()

        # Add current vote
        self._votes[track_id].append((now, match_result))

        # Purge votes outside the time window
        self._votes[track_id] = [
            (t, r) for t, r in self._votes[track_id]
            if now - t <= self.vote_window_sec
        ]

        votes = self._votes[track_id]

        if len(votes) < self.vote_frames:
            return None  # not enough votes yet

        # Check if all votes in window agree on the same identity
        names = [r["name"] for _, r in votes]
        most_common = max(set(names), key=names.count)
        agreement = names.count(most_common)

        if agreement >= self.vote_frames:
            # Consensus reached — return the most recent matching result
            final = next(
                r for _, r in reversed(votes)
                if r["name"] == most_common
            )
            self.clear(track_id)  # reset after decision fires
            logger.info(
                f"[Voter] Decision for track {track_id}: "
                f"{final['name']} ({final['confidence']:.2f}) "
                f"— {final['access'].upper()}"
            )
            return final

        return None

    def clear(self, track_id: str):
        """Reset votes for a track — called after decision fires."""
        self._votes.pop(track_id, None)

    def clear_all(self):
        """Reset all votes — call on system restart."""
        self._votes.clear()
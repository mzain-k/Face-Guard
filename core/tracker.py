import numpy as np
import time
import logging

logger = logging.getLogger(__name__)

class Track:
    """Represents a single tracked face across frames."""

    def __init__(self, track_id: int, bbox: list, embedding: np.ndarray):
        self.track_id = track_id
        self.bbox = bbox
        self.embedding = embedding
        self.last_seen = time.time()
        self.hit_count = 1

    def update(self, bbox: list, embedding: np.ndarray):
        self.bbox = bbox
        self.embedding = embedding
        self.last_seen = time.time()
        self.hit_count += 1

    def is_stale(self, max_age_sec: float = 3.0) -> bool:
        return (time.time() - self.last_seen) > max_age_sec


class FaceTracker:
    """
    Lightweight centroid-based face tracker.
    Assigns consistent track IDs to faces across frames
    using bounding box IoU matching — no PyTorch required.

    Why not ByteTrack:
    - ByteTrack requires PyTorch (~2GB) as a dependency
    - For 1-4 people in a security camera scene, centroid
      matching is more than sufficient
    - Zero extra dependencies
    """

    def __init__(self, iou_threshold: float = 0.3, max_age_sec: float = 3.0):
        self.iou_threshold = iou_threshold
        self.max_age_sec = max_age_sec
        self._tracks: dict[int, Track] = {}
        self._next_id = 0

    def update(self, faces: list) -> list:
        """
        Match detected faces to existing tracks.

        Args:
            faces: list of insightface face objects with .bbox and .embedding

        Returns:
            list of (track_id, face) tuples
        """
        # Remove stale tracks
        stale = [tid for tid, t in self._tracks.items() if t.is_stale(self.max_age_sec)]
        for tid in stale:
            logger.debug(f"Track {tid} expired.")
            del self._tracks[tid]

        if not faces:
            return []

        results = []
        matched_track_ids = set()

        for face in faces:
            bbox = [int(v) for v in face.bbox]
            embedding = face.embedding
            best_iou = 0.0
            best_tid = None

            for tid, track in self._tracks.items():
                if tid in matched_track_ids:
                    continue
                iou = self._iou(bbox, track.bbox)
                if iou > best_iou:
                    best_iou = iou
                    best_tid = tid

            if best_tid is not None and best_iou >= self.iou_threshold:
                # Match found — update existing track
                self._tracks[best_tid].update(bbox, embedding)
                matched_track_ids.add(best_tid)
                results.append((best_tid, face))
            else:
                # No match — create new track
                new_id = self._next_id
                self._tracks[new_id] = Track(new_id, bbox, embedding)
                self._next_id += 1
                matched_track_ids.add(new_id)
                results.append((new_id, face))

        return results

    def _iou(self, bbox_a: list, bbox_b: list) -> float:
        """
        Intersection over Union between two bounding boxes.
        bbox format: [x1, y1, x2, y2]
        """
        ax1, ay1, ax2, ay2 = bbox_a
        bx1, by1, bx2, by2 = bbox_b

        inter_x1 = max(ax1, bx1)
        inter_y1 = max(ay1, by1)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)

        inter_w = max(0, inter_x2 - inter_x1)
        inter_h = max(0, inter_y2 - inter_y1)
        inter_area = inter_w * inter_h

        area_a = (ax2 - ax1) * (ay2 - ay1)
        area_b = (bx2 - bx1) * (by2 - by1)
        union_area = area_a + area_b - inter_area

        if union_area == 0:
            return 0.0
        return inter_area / union_area

    def clear(self):
        self._tracks.clear()
        self._next_id = 0
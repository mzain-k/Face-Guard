import os
import logging
from datetime import datetime, timedelta
from dashboard.backend.db import SessionLocal, Event

logger = logging.getLogger(__name__)

SNAPSHOTS_DIR = os.path.join(os.path.dirname(__file__), "../data/snapshots")


def run_retention(snapshot_days: int = 30, log_days: int = 90):
    """
    Auto-delete old snapshots and event log entries.
    Call once at startup and optionally on a schedule.
    """
    _clean_snapshots(snapshot_days)
    _clean_db_logs(log_days)


def _clean_snapshots(days: int):
    """Delete snapshot images older than `days` days."""
    if not os.path.exists(SNAPSHOTS_DIR):
        return

    cutoff = datetime.now() - timedelta(days=days)
    deleted = 0

    for filename in os.listdir(SNAPSHOTS_DIR):
        path = os.path.join(SNAPSHOTS_DIR, filename)
        if not os.path.isfile(path):
            continue
        modified = datetime.fromtimestamp(os.path.getmtime(path))
        if modified < cutoff:
            os.remove(path)
            deleted += 1

    if deleted:
        logger.info(f"Retention: deleted {deleted} snapshots older than {days} days.")
    else:
        logger.info(f"Retention: no snapshots to clean.")


def _clean_db_logs(days: int):
    """Delete event log entries older than `days` days."""
    cutoff = datetime.now() - timedelta(days=days)
    db = SessionLocal()
    try:
        deleted = db.query(Event).filter(Event.timestamp < cutoff).delete()
        db.commit()
        if deleted:
            logger.info(f"Retention: deleted {deleted} event log entries older than {days} days.")
        else:
            logger.info(f"Retention: no log entries to clean.")
    finally:
        db.close()
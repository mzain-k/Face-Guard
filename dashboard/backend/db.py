import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "../../data/faceguard.db")
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Event(Base):
    __tablename__ = "events"
    id           = Column(Integer, primary_key=True, index=True)
    timestamp    = Column(DateTime, default=datetime.now)
    camera_id    = Column(String)
    name         = Column(String)
    access       = Column(String)
    confidence   = Column(Float)
    action       = Column(String)
    snapshot_path = Column(String, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)


def log_event(camera_id: str, name: str, access: str,
              confidence: float, action: str, snapshot_path: str = None):
    db = SessionLocal()
    try:
        event = Event(
            camera_id=camera_id,
            name=name,
            access=access,
            confidence=confidence,
            action=action,
            snapshot_path=snapshot_path
        )
        db.add(event)
        db.commit()
    finally:
        db.close()
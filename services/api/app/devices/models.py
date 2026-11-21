"""SQLAlchemy models for Device Management [M1]."""
from datetime import datetime, timezone
import uuid
from typing import Optional, Dict, Any

from sqlalchemy import Column, String, Float, Boolean, DateTime, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class CameraDeviceModel(Base):
    """SQLAlchemy model representing a registered camera device."""
    __tablename__ = "camera_devices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    status = Column(String(32), nullable=False, default="OFFLINE", index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    device_metadata = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_seen_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert database model to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "status": self.status,
            "is_active": self.is_active,
            "device_metadata": self.device_metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
        }


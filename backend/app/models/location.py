from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    location_type_id = Column(Integer, ForeignKey("location_types.id"), nullable=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    floor = Column(String(20), nullable=True)
    room_number = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    location_type = relationship("LocationType", back_populates="locations")
    site = relationship("Site", backref="locations")
    assets = relationship("Asset", back_populates="location")

    def __repr__(self):
        return f"<Location(id={self.id}, name='{self.name}', site_id={self.site_id})>"

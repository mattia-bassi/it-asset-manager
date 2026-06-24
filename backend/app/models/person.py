from sqlalchemy import Boolean, Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Person(Base):
    __tablename__ = "people"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False, index=True)
    last_name = Column(String(100), nullable=False, index=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="SET NULL"), nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    extension = Column(String(20), nullable=True)
    mobile_phone = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationship
    site = relationship("Site", backref="people")

    @property
    def full_name(self) -> str:
        """Ritorna il nome completo."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Person(id={self.id}, name='{self.full_name}')>"

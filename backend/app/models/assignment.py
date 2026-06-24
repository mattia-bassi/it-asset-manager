from sqlalchemy import Column, Integer, String, Text, Date, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("people.id", ondelete="SET NULL"), nullable=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True)
    assignment_date = Column(Date, nullable=False, index=True)
    return_date = Column(Date, nullable=True, index=True)
    assignment_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, server_default='attivo', index=True)
    notes = Column(Text, nullable=True)
    document_path = Column(String(500), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    person = relationship("Person", backref="assignments")
    location = relationship("Location", lazy="select")
    items = relationship("AssignmentItem", back_populates="assignment", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])

    @property
    def is_active(self) -> bool:
        """Ritorna True se l'assegnazione è attiva."""
        return self.status == 'attivo' and self.return_date is None

    @property
    def assignment_number(self) -> str:
        """Genera il numero assegnazione formato ASS-YYYY-NNN."""
        if self.assignment_date:
            year = self.assignment_date.year
            return f"ASS-{year}-{self.id:03d}"
        return f"ASS-{self.id:03d}"

    def __repr__(self):
        return f"<Assignment(id={self.id}, person_id={self.person_id}, status='{self.status}')>"


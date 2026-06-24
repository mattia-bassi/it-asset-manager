from sqlalchemy import Column, Integer, String, TIMESTAMP, Enum as SQLEnum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum


class SimStatus(str, enum.Enum):
    disponibile = "disponibile"
    assegnata = "assegnata"
    disattivata = "disattivata"


class Sim(Base):
    __tablename__ = "sims"
    
    id = Column(Integer, primary_key=True, index=True)
    seriale = Column(String(100), unique=True, nullable=False, index=True)
    operatore = Column(String(50), nullable=False)  # TIM, Vodafone, Wind, ecc.
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="SET NULL"), nullable=True, index=True)
    numero_telefono = Column(String(20), unique=True, nullable=False)
    pin_criptato = Column(String(255), nullable=False)  # PIN criptato
    puk_criptato = Column(String(255), nullable=False)  # PUK criptato
    status = Column(SQLEnum(SimStatus), default=SimStatus.disponibile, nullable=False)
    person_id = Column(Integer, ForeignKey("people.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    site = relationship("Site", backref="sims")
    person = relationship("Person", backref="sims", foreign_keys=[person_id])

    def __repr__(self):
        return f"<Sim(id={self.id}, seriale='{self.seriale}', numero='{self.numero_telefono}')>"

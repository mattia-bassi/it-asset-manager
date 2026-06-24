from sqlalchemy import Column, Integer, String, Date, TIMESTAMP, Enum as SQLEnum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum


class BadgeStatus(str, enum.Enum):
    attivo = "attivo"
    disattivo = "disattivo"
    smarrito = "smarrito"


class BadgeType(str, enum.Enum):
    dipendente = "dipendente"
    visitatore = "visitatore"
    temporaneo = "temporaneo"


class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    numero_badge = Column(String(50), unique=True, nullable=False, index=True)
    tipo = Column(SQLEnum(BadgeType), nullable=False)
    status = Column(SQLEnum(BadgeStatus), default=BadgeStatus.attivo, nullable=False)
    data_emissione = Column(Date, nullable=False)
    data_scadenza = Column(Date, nullable=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="SET NULL"), nullable=True, index=True)
    person_id = Column(Integer, ForeignKey("people.id", ondelete="SET NULL"), nullable=True, index=True)
    notes = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Timestamps
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    site = relationship("Site", backref="badges")
    person = relationship("Person", backref="badges", foreign_keys=[person_id])

    def __repr__(self):
        return f"<Badge(id={self.id}, numero='{self.numero_badge}', tipo='{self.tipo}')>"

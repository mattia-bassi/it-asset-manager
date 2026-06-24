from sqlalchemy import Boolean, Column, Integer, String, Text, TIMESTAMP, ForeignKey, JSON, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    
    # IDENTIFICATIVI
    asset_code = Column(String(50), unique=True, nullable=True, index=True)
    serial_number = Column(String(100), nullable=False, index=True)
    mac_address = Column(String(17), nullable=True, index=True)
    
    # TIPO E PRODOTTO
    asset_type_id = Column(Integer, ForeignKey("asset_types.id", ondelete="RESTRICT"), nullable=False, index=True)
    manufacturer = Column(String(100), nullable=False, index=True)
    model = Column(String(100), nullable=False, index=True)
    
    # ASSEGNAZIONE
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="SET NULL"), nullable=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True, index=True)
    person_id = Column(Integer, ForeignKey("people.id", ondelete="SET NULL"), nullable=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True, index=True)

    # STATO E CICLO VITA
    status = Column(String(50), nullable=False, server_default="disponibile", index=True)
    purchase_date = Column(Date, nullable=True)
    warranty_expiry = Column(Date, nullable=True)
    
    # SPECIFICHE TECNICHE (JSON)
    specifications = Column(JSON, nullable=True)
    
    # ALTRO
    notes = Column(Text, nullable=True)
    qr_code = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    asset_type = relationship("AssetType", back_populates="assets")
    site = relationship("Site", backref="assets")
    location = relationship("Location", back_populates="assets")
    person = relationship("Person", backref="assets")
    supplier = relationship("Supplier", back_populates="assets")

    @property
    def full_name(self) -> str:
        """Ritorna il nome completo dell'asset."""
        return f"{self.manufacturer} {self.model} ({self.serial_number})"

    def __repr__(self):
        return f"<Asset(id={self.id}, code='{self.asset_code}', serial='{self.serial_number}')>"

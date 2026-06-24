from sqlalchemy import Boolean, Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class InventorySku(Base):
    __tablename__ = "inventory_skus"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False, index=True)
    device = Column(String(200), nullable=False, index=True)
    brand = Column(String(100), nullable=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="SET NULL"), nullable=True, index=True)
    quantity = Column(Integer, nullable=False, default=0)
    min_quantity = Column(Integer, nullable=False, default=5)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    site = relationship("Site", backref="inventory_skus")

    @property
    def is_low_stock(self) -> bool:
        """Ritorna True se la quantità è sotto la soglia minima."""
        return self.quantity <= self.min_quantity

    @property
    def full_name(self) -> str:
        """Ritorna il nome completo del materiale."""
        if self.brand:
            return f"{self.brand} {self.device}"
        return self.device

    def __repr__(self):
        return f"<InventorySku(id={self.id}, device='{self.device}', qty={self.quantity})>"


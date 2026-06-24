from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class AssignmentItem(Base):
    __tablename__ = "assignment_items"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    item_type = Column(String(20), nullable=False, index=True)
    is_returned = Column(Boolean, nullable=False, server_default='0', index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="RESTRICT"), nullable=True, index=True)
    inventory_sku_id = Column(Integer, ForeignKey("inventory_skus.id", ondelete="RESTRICT"), nullable=True, index=True)
    sim_id = Column(Integer, ForeignKey("sims.id", ondelete="RESTRICT"), nullable=True, index=True)
    badge_id = Column(Integer, ForeignKey("badges.id", ondelete="SET NULL"), nullable=True, index=True)
    quantity = Column(Integer, nullable=False, server_default='1')
    notes = Column(Text, nullable=True)

    # Relationships
    assignment = relationship("Assignment", back_populates="items")
    asset = relationship("Asset", backref="assignment_items")
    inventory_sku = relationship("InventorySku", backref="assignment_items")
    sim = relationship("Sim", backref="assignment_items")
    badge = relationship("Badge", backref="assignment_items", foreign_keys=[badge_id])

    @property
    def item_description(self) -> str:
        """Ritorna una descrizione dell'item."""
        if self.item_type == 'asset' and self.asset:
            return f"{self.asset.manufacturer} {self.asset.model} (SN: {self.asset.serial_number})"
        elif self.item_type == 'inventory' and self.inventory_sku:
            return f"{self.inventory_sku.full_name} x{self.quantity}"
        elif self.item_type == 'sim' and self.sim:
            return f"SIM {self.sim.operatore} - {self.sim.numero_telefono}"
        return "Item sconosciuto"

    def __repr__(self):
        return f"<AssignmentItem(id={self.id}, type='{self.item_type}', qty={self.quantity})>"


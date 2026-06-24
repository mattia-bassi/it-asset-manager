from sqlalchemy import Boolean, Column, Integer, String, Text, TIMESTAMP, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class AssetType(Base):
    __tablename__ = "asset_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("asset_types.id", ondelete="CASCADE"), nullable=True, index=True)
    description = Column(Text, nullable=True)
    fields_schema = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    parent = relationship("AssetType", remote_side=[id], backref="children")
    assets = relationship("Asset", back_populates="asset_type")

    def __repr__(self):
        return f"<AssetType(id={self.id}, name='{self.name}')>"


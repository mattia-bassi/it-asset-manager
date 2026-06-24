from sqlalchemy import Boolean, Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.sql import func
from app.models.base import Base


class DocumentTemplate(Base):
    __tablename__ = "document_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    logo_path = Column(String(500), nullable=True)
    footer_path = Column(String(500), nullable=True)
    is_default = Column(Boolean, nullable=False, default=False, server_default="0", index=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="1", index=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(
        TIMESTAMP, 
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    def __repr__(self):
        return f"<DocumentTemplate(id={self.id}, name='{self.name}', is_default={self.is_default})>"

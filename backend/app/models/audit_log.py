from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base

class AuditLog(Base):
    """Log delle azioni importanti per audit trail"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # 'asset', 'assignment', etc
    entity_id = Column(Integer, nullable=True, index=True)
    details = Column(Text, nullable=True)  # JSON string con dettagli aggiuntivi
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Campi aggiunti per Fase 2 Audit Log
    username = Column(String(100), nullable=True, index=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

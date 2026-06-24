from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AuditLogOut(BaseModel):
    """Schema per la risposta di un singolo audit log"""
    id: int
    user_id: Optional[int] = None
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    details: Optional[str] = None
    created_at: datetime
    username: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Schema per la risposta paginata di audit logs"""
    items: list[AuditLogOut]
    total: int
    skip: int
    limit: int


class AuditLogFilters(BaseModel):
    """Schema per i filtri di ricerca audit logs"""
    action: Optional[str] = Field(None, description="Filtra per azione (CREATE, UPDATE, DELETE, etc.)")
    entity_type: Optional[str] = Field(None, description="Filtra per tipo entità (asset, person, user, etc.)")
    entity_id: Optional[int] = Field(None, description="Filtra per ID entità specifica")
    user_id: Optional[int] = Field(None, description="Filtra per ID utente")
    username: Optional[str] = Field(None, description="Filtra per username (ricerca parziale)")
    date_from: Optional[datetime] = Field(None, description="Data inizio range (ISO 8601)")
    date_to: Optional[datetime] = Field(None, description="Data fine range (ISO 8601)")
    search: Optional[str] = Field(None, description="Ricerca testuale in details, username, action")

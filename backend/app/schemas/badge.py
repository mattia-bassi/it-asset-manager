from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from enum import Enum


class BadgeStatus(str, Enum):
    attivo = "attivo"
    disattivo = "disattivo"
    smarrito = "smarrito"


class BadgeType(str, Enum):
    dipendente = "dipendente"
    visitatore = "visitatore"
    temporaneo = "temporaneo"


class BadgeBase(BaseModel):
    numero_badge: str = Field(..., min_length=1, max_length=50, description="Numero identificativo badge")
    tipo: BadgeType
    status: BadgeStatus = BadgeStatus.attivo
    data_emissione: date
    data_scadenza: Optional[date] = None
    site_id: Optional[int] = None
    person_id: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=500)
    is_active: bool = True


class BadgeCreate(BadgeBase):
    pass


class BadgeUpdate(BaseModel):
    numero_badge: Optional[str] = Field(None, min_length=1, max_length=50)
    tipo: Optional[BadgeType] = None
    status: Optional[BadgeStatus] = None
    data_emissione: Optional[date] = None
    data_scadenza: Optional[date] = None
    site_id: Optional[int] = None
    person_id: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class Badge(BadgeBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BadgeList(BaseModel):
    items: list[Badge]
    total: int
    page: int
    page_size: int
    pages: int

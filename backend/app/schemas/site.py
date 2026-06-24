from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# Schema base condiviso
class SiteBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Nome della sede")
    address: Optional[str] = Field(None, description="Indirizzo completo")
    city: Optional[str] = Field(None, max_length=100, description="Città")
    postal_code: Optional[str] = Field(None, max_length=20, description="CAP")
    country: Optional[str] = Field(None, max_length=100, description="Paese")
    centralino: Optional[str] = Field(None, max_length=50, description="Centralino/Prefisso (es. +39 06 12345)")
    notes: Optional[str] = Field(None, description="Note aggiuntive")
    is_active: bool = Field(True, description="Sede attiva")

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Il nome della sede non può essere vuoto')
        return v.strip()


# Schema per creazione (POST)
class SiteCreate(SiteBase):
    pass


# Schema per aggiornamento (PUT/PATCH)
class SiteUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    centralino: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError('Il nome della sede non può essere vuoto')
        return v.strip() if v else None


# Schema per risposta (GET)
class Site(SiteBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Schema per lista con paginazione
class SiteList(BaseModel):
    items: list[Site]
    total: int
    page: int
    page_size: int
    pages: int


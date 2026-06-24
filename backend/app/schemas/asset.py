from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# Schema base condiviso
class AssetBase(BaseModel):
    asset_code: Optional[str] = Field(None, max_length=50, description="Codice asset aziendale")
    serial_number: str = Field(..., min_length=1, max_length=100, description="Numero seriale")
    mac_address: Optional[str] = Field(None, max_length=17, description="MAC Address")
    
    asset_type_id: int = Field(..., description="ID tipo asset")
    manufacturer: str = Field(..., min_length=1, max_length=100, description="Produttore")
    model: str = Field(..., min_length=1, max_length=100, description="Modello")
    
    site_id: Optional[int] = Field(None, description="ID sede")
    person_id: Optional[int] = Field(None, description="ID persona assegnataria")
    
    status: str = Field("disponibile", max_length=50, description="Stato asset")
    purchase_date: Optional[date] = Field(None, description="Data acquisto")
    warranty_expiry: Optional[date] = Field(None, description="Scadenza garanzia")
    
    specifications: Optional[dict] = Field(None, description="Specifiche tecniche JSON")
    notes: Optional[str] = Field(None, description="Note")
    is_active: bool = Field(True, description="Asset attivo")

    @field_validator('serial_number', 'manufacturer', 'model')
    @classmethod
    def fields_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('I campi obbligatori non possono essere vuoti')
        return v.strip()

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed_statuses = ['disponibile', 'assegnato', 'manutenzione', 'dismissione', 'dismesso']
        if v not in allowed_statuses:
            raise ValueError(f'Status deve essere uno tra: {", ".join(allowed_statuses)}')
        return v


# Schema per creazione (POST)
class AssetCreate(AssetBase):
    pass


# Schema per aggiornamento (PUT/PATCH)
class AssetUpdate(BaseModel):
    asset_code: Optional[str] = Field(None, max_length=50)
    serial_number: Optional[str] = Field(None, min_length=1, max_length=100)
    mac_address: Optional[str] = Field(None, max_length=17)
    
    asset_type_id: Optional[int] = None
    manufacturer: Optional[str] = Field(None, min_length=1, max_length=100)
    model: Optional[str] = Field(None, min_length=1, max_length=100)
    
    site_id: Optional[int] = None
    person_id: Optional[int] = None
    
    status: Optional[str] = Field(None, max_length=50)
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    
    specifications: Optional[dict] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator('serial_number', 'manufacturer', 'model')
    @classmethod
    def fields_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError('I campi obbligatori non possono essere vuoti')
        return v.strip() if v else None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed_statuses = ['disponibile', 'assegnato', 'manutenzione', 'dismissione', 'dismesso']
            if v not in allowed_statuses:
                raise ValueError(f'Status deve essere uno tra: {", ".join(allowed_statuses)}')
        return v


# Schema per risposta (GET) - base
class Asset(AssetBase):
    id: int
    qr_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Schema per risposta con dettagli completi
class AssetWithDetails(Asset):
    asset_type_name: Optional[str] = Field(None, description="Nome tipo asset")
    site_name: Optional[str] = Field(None, description="Nome sede")
    person_name: Optional[str] = Field(None, description="Nome persona")
    location_id: Optional[int] = Field(None, description="ID locazione assegnataria")
    location_name: Optional[str] = Field(None, description="Nome locazione")
    supplier_id: Optional[int] = Field(None, description="ID fornitore")
    supplier_name: Optional[str] = Field(None, description="Nome fornitore")


# Schema per lista con paginazione
class AssetList(BaseModel):
    items: list[AssetWithDetails]
    total: int
    page: int
    page_size: int
    pages: int


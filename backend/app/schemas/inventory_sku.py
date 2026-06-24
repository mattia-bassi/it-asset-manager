from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# Schema base condiviso
class InventorySkuBase(BaseModel):
    category: str = Field(..., min_length=1, max_length=100, description="Categoria")
    device: str = Field(..., min_length=1, max_length=200, description="Dispositivo")
    brand: Optional[str] = Field(None, max_length=100, description="Marca (opzionale)")
    site_id: Optional[int] = Field(None, description="ID sede dove si trova il materiale")
    quantity: int = Field(0, ge=0, description="Quantità disponibile")
    min_quantity: int = Field(5, ge=0, description="Soglia minima per alert")
    notes: Optional[str] = Field(None, description="Note aggiuntive")
    is_active: bool = Field(True, description="Materiale attivo")

    @field_validator('category', 'device')
    @classmethod
    def fields_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Categoria e dispositivo non possono essere vuoti')
        return v.strip()

    @field_validator('quantity', 'min_quantity')
    @classmethod
    def validate_quantities(cls, v: int) -> int:
        if v < 0:
            raise ValueError('Le quantità non possono essere negative')
        return v


# Schema per creazione (POST)
class InventorySkuCreate(InventorySkuBase):
    pass


# Schema per aggiornamento (PUT/PATCH)
class InventorySkuUpdate(BaseModel):
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    device: Optional[str] = Field(None, min_length=1, max_length=200)
    brand: Optional[str] = Field(None, max_length=100)
    site_id: Optional[int] = Field(None, description="ID sede")
    quantity: Optional[int] = Field(None, ge=0)
    min_quantity: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator('category', 'device')
    @classmethod
    def fields_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError('Categoria e dispositivo non possono essere vuoti')
        return v.strip() if v else None

    @field_validator('quantity', 'min_quantity')
    @classmethod
    def validate_quantities(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError('Le quantità non possono essere negative')
        return v


# Schema per aggiornamento solo quantità
class InventorySkuQuantityUpdate(BaseModel):
    quantity: int = Field(..., description="Nuova quantità")
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        if v < 0:
            raise ValueError('La quantità non può essere negativa')
        return v


# Schema per risposta (GET)
class InventorySku(InventorySkuBase):
    id: int
    is_low_stock: bool = Field(..., description="True se sotto soglia minima")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Schema per lista con paginazione
class InventorySkuList(BaseModel):
    items: list[InventorySku]
    total: int
    page: int
    page_size: int
    pages: int
    low_stock_count: int = Field(..., description="Numero di materiali sotto soglia")


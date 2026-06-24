from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# Schema base condiviso
class AssetTypeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Nome del tipo")
    parent_id: Optional[int] = Field(None, description="ID del tipo padre")
    description: Optional[str] = Field(None, description="Descrizione")
    fields_schema: Optional[dict] = Field(None, description="Schema dei campi JSON")
    is_active: bool = Field(True, description="Tipo attivo")


# Schema per creazione (POST)
class AssetTypeCreate(AssetTypeBase):
    pass


# Schema per aggiornamento (PUT/PATCH)
class AssetTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    parent_id: Optional[int] = None
    description: Optional[str] = None
    fields_schema: Optional[dict] = None
    is_active: Optional[bool] = None


# Schema per risposta (GET)
class AssetType(AssetTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Schema con informazioni sul padre
class AssetTypeWithParent(AssetType):
    parent_name: Optional[str] = Field(None, description="Nome del tipo padre")


# Schema per lista con paginazione
class AssetTypeList(BaseModel):
    items: list[AssetTypeWithParent]
    total: int
    page: int
    page_size: int
    pages: int


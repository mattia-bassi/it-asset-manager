from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DocumentTemplateBase(BaseModel):
    name: str = Field(..., max_length=100, description="Nome del template")
    description: Optional[str] = Field(None, description="Descrizione del template")
    logo_path: Optional[str] = Field(None, max_length=500, description="Path del logo")
    footer_path: Optional[str] = Field(None, max_length=500, description="Path del footer")
    is_default: bool = Field(False, description="Template predefinito")
    is_active: bool = Field(True, description="Template attivo")


class DocumentTemplateCreate(DocumentTemplateBase):
    pass


class DocumentTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    logo_path: Optional[str] = Field(None, max_length=500)
    footer_path: Optional[str] = Field(None, max_length=500)
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class DocumentTemplateInDB(DocumentTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentTemplate(DocumentTemplateInDB):
    pass

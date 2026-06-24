from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, EmailStr


# Schema base condiviso
class PersonBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100, description="Nome")
    last_name: str = Field(..., min_length=1, max_length=100, description="Cognome")
    site_id: Optional[int] = Field(None, description="ID della sede")
    email: Optional[EmailStr] = Field(None, description="Email")
    extension: Optional[str] = Field(None, max_length=20, description="Interno telefonico")
    mobile_phone: Optional[str] = Field(None, max_length=50, description="Numero cellulare")
    notes: Optional[str] = Field(None, description="Note aggiuntive")
    is_active: bool = Field(True, description="Persona attiva")

    @field_validator('first_name', 'last_name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Nome e cognome non possono essere vuoti')
        return v.strip()


# Schema per creazione (POST)
class PersonCreate(PersonBase):
    pass


# Schema per aggiornamento (PUT/PATCH)
class PersonUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    site_id: Optional[int] = None
    email: Optional[EmailStr] = None
    extension: Optional[str] = Field(None, max_length=20)
    mobile_phone: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator('first_name', 'last_name')
    @classmethod
    def name_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError('Nome e cognome non possono essere vuoti')
        return v.strip() if v else None


# Schema per risposta (GET) - base
class Person(PersonBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Schema per risposta con dettagli sede
class PersonWithSite(Person):
    site_name: Optional[str] = Field(None, description="Nome della sede")
    linked_username: Optional[str] = Field(None, description="Username account collegato")


# Schema per merge di due persone
class PersonMerge(BaseModel):
    source_id: int = Field(..., description="ID della persona da unire (verrà disattivata)")
    target_id: int = Field(..., description="ID della persona destinazione")
    merge_notes: bool = Field(True, description="Unire anche le note")


# Schema per lista con paginazione
class PersonList(BaseModel):
    items: list[PersonWithSite]
    total: int
    page: int
    page_size: int
    pages: int


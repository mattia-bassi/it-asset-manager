from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from app.schemas.assignment_item import AssignmentItem, AssignmentItemCreate


# Schema base condiviso
class AssignmentBase(BaseModel):
    person_id: Optional[int] = Field(None, description="ID persona")
    location_id: Optional[int] = Field(None, description="ID locazione")
    assignment_date: date = Field(..., description="Data assegnazione")
    return_date: Optional[date] = Field(None, description="Data riconsegna (NULL se attivo)")
    assignment_type: str = Field(..., description="Tipo: 'assegnazione', 'riconsegna', 'sostituzione'")
    status: str = Field('attivo', description="Stato: 'attivo' o 'completato'")
    notes: Optional[str] = Field(None, description="Note generali")

    @field_validator('assignment_type')
    @classmethod
    def validate_assignment_type(cls, v: str) -> str:
        allowed = ['assegnazione', 'riconsegna', 'sostituzione']
        if v not in allowed:
            raise ValueError(f"assignment_type deve essere uno tra: {', '.join(allowed)}")
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ['attivo', 'completato']:
            raise ValueError("status deve essere 'attivo' o 'completato'")
        return v


# Schema per creazione (POST)
class AssignmentCreate(AssignmentBase):
    items: list[AssignmentItemCreate] = Field(default_factory=list, description="Lista items da assegnare")
    returned_items: Optional[list[AssignmentItemCreate]] = Field(default=None, description="Lista items restituiti (per sostituzione/riconsegna)")

    @model_validator(mode='after')
    def validate_recipient(self) -> 'AssignmentCreate':
        has_person = self.person_id is not None
        has_location = self.location_id is not None
        if not has_person and not has_location:
            raise ValueError('Specificare person_id oppure location_id')
        if has_person and has_location:
            raise ValueError('Specificare solo person_id oppure location_id, non entrambi')
        return self


# Schema per aggiornamento (PUT/PATCH)
class AssignmentUpdate(BaseModel):
    person_id: Optional[int] = None
    location_id: Optional[int] = None
    document_path: Optional[str] = None
    return_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ['attivo', 'completato']:
            raise ValueError("status deve essere 'attivo' o 'completato'")
        return v


# Schema per risposta (GET)
class Assignment(AssignmentBase):
    id: int
    location_name: Optional[str] = Field(None, description="Nome locazione (se destinatario è una locazione)")
    document_path: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool = Field(..., description="True se assegnazione attiva")
    assignment_number: str = Field(..., description="Numero assegnazione formato ASS-YYYY-NNN")
    items: list[AssignmentItem] = Field(default_factory=list, description="Items assegnati")

    model_config = {"from_attributes": True}


# Schema con dettagli persona/locazione
class AssignmentWithDetails(Assignment):
    person_name: Optional[str] = Field(None, description="Nome completo persona (se destinatario è persona)")
    person_email: Optional[str] = Field(None, description="Email persona")
    location_name: Optional[str] = Field(None, description="Nome locazione (se destinatario è locazione)")
    creator_name: Optional[str] = Field(None, description="Nome operatore che ha creato")


# Schema per lista con paginazione
class AssignmentList(BaseModel):
    items: list[AssignmentWithDetails]
    total: int
    page: int
    page_size: int
    pages: int
    active_count: int = Field(..., description="Numero di assegnazioni attive")


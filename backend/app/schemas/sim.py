from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class SimStatus(str, Enum):
    """Status possibili per una SIM"""
    disponibile = "disponibile"
    assegnata = "assegnata"
    disattivata = "disattivata"


class SimBase(BaseModel):
    """Schema base per SIM"""
    seriale: str = Field(..., min_length=1, max_length=100, description="Seriale SIM univoco")
    operatore: str = Field(..., min_length=1, max_length=50, description="Operatore telefonico (es: TIM, Vodafone, Wind)")
    site_id: Optional[int] = Field(None, description="ID sede dove si trova la SIM")
    numero_telefono: str = Field(..., min_length=1, max_length=20, description="Numero di telefono")
    
    @field_validator('numero_telefono')
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """Valida formato numero telefono (rimuove spazi e caratteri speciali)"""
        # Rimuovi spazi, trattini, parentesi
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        if not cleaned:
            raise ValueError('Numero telefono deve contenere almeno una cifra')
        return cleaned


class SimCreate(SimBase):
    """Schema per creazione SIM"""
    pin: str = Field(..., min_length=4, max_length=8, description="PIN SIM (4-8 cifre)")
    puk: str = Field(..., min_length=8, max_length=8, description="PUK SIM (8 cifre)")
    status: SimStatus = Field(default=SimStatus.disponibile, description="Status iniziale")
    
    @field_validator('pin')
    @classmethod
    def validate_pin(cls, v: str) -> str:
        """Valida che il PIN sia numerico"""
        if not v.isdigit():
            raise ValueError('PIN deve contenere solo cifre')
        if len(v) < 4 or len(v) > 8:
            raise ValueError('PIN deve essere tra 4 e 8 cifre')
        return v
    
    @field_validator('puk')
    @classmethod
    def validate_puk(cls, v: str) -> str:
        """Valida che il PUK sia numerico e 8 cifre"""
        if not v.isdigit():
            raise ValueError('PUK deve contenere solo cifre')
        if len(v) != 8:
            raise ValueError('PUK deve essere esattamente 8 cifre')
        return v


class SimUpdate(BaseModel):
    """Schema per aggiornamento SIM (tutti i campi opzionali)"""
    seriale: Optional[str] = Field(None, min_length=1, max_length=100)
    operatore: Optional[str] = Field(None, min_length=1, max_length=50)
    site_id: Optional[int] = Field(None, description="ID sede dove si trova la SIM")
    numero_telefono: Optional[str] = Field(None, min_length=1, max_length=20)
    pin: Optional[str] = Field(None, min_length=4, max_length=8, description="Nuovo PIN (verrà criptato)")
    puk: Optional[str] = Field(None, min_length=8, max_length=8, description="Nuovo PUK (verrà criptato)")
    status: Optional[SimStatus] = None
    
    @field_validator('numero_telefono')
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        if not cleaned:
            raise ValueError('Numero telefono deve contenere almeno una cifra')
        return cleaned
    
    @field_validator('pin')
    @classmethod
    def validate_pin(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v.isdigit():
            raise ValueError('PIN deve contenere solo cifre')
        if len(v) < 4 or len(v) > 8:
            raise ValueError('PIN deve essere tra 4 e 8 cifre')
        return v
    
    @field_validator('puk')
    @classmethod
    def validate_puk(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v.isdigit():
            raise ValueError('PUK deve contenere solo cifre')
        if len(v) != 8:
            raise ValueError('PUK deve essere esattamente 8 cifre')
        return v


class SimResponse(SimBase):
    """Schema per risposta API (senza PIN/PUK esposti)"""
    id: int
    person_id: Optional[int] = None
    status: SimStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Campi persona (populated se SIM è assegnata)
    person_first_name: Optional[str] = None
    person_last_name: Optional[str] = None

    # PIN/PUK non vengono mai esposti nelle risposte normali
    # Saranno disponibili solo tramite endpoint dedicato con autenticazione

    model_config = {"from_attributes": True}


class SimWithCredentials(SimResponse):
    """Schema per risposta con credenziali (solo per admin)"""
    pin: str = Field(..., description="PIN decriptato")
    puk: str = Field(..., description="PUK decriptato")


class SimListResponse(BaseModel):
    """Schema per lista paginata di SIM"""
    items: list[SimResponse]
    total: int
    page: int
    page_size: int
    pages: int

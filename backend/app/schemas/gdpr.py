from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# ============================================================================
# GDPR Art. 15 - Right of Access (Diritto di Accesso)
# ============================================================================

class GDPRMyDataResponse(BaseModel):
    """Response per export completo dati utente (GDPR Art. 15)"""
    user_id: int
    username: str
    email: Optional[str]
    full_name: Optional[str]
    role: str
    created_at: datetime

    # Dati collegati
    person: Optional[Dict[str, Any]] = None
    assets_assigned: List[Dict[str, Any]] = Field(default_factory=list)
    assignments_history: List[Dict[str, Any]] = Field(default_factory=list)
    sims_assigned: List[Dict[str, Any]] = Field(default_factory=list)
    badges_assigned: List[Dict[str, Any]] = Field(default_factory=list)
    audit_logs: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata export
    exported_at: datetime
    export_format: str = "JSON"

    class Config:
        from_attributes = True


# ============================================================================
# GDPR Art. 20 - Right to Data Portability (Portabilità)
# ============================================================================

class GDPRPortabilityResponse(BaseModel):
    """Response per esportazione dati in formato portabile (GDPR Art. 20)"""
    user_id: int
    export_date: datetime
    data_format: str = "JSON"

    # Dati in formato machine-readable
    user_data: Dict[str, Any]
    person_data: Optional[Dict[str, Any]] = None
    assets: List[Dict[str, Any]] = Field(default_factory=list)
    assignments: List[Dict[str, Any]] = Field(default_factory=list)
    sims: List[Dict[str, Any]] = Field(default_factory=list)
    badges: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ============================================================================
# GDPR Art. 16 - Right to Rectification (Rettifica)
# ============================================================================

class GDPRRectificationRequest(BaseModel):
    """Request per rettifica dati personali (GDPR Art. 16)"""
    email: Optional[str] = Field(None, description="Nuovo indirizzo email")
    full_name: Optional[str] = Field(None, description="Nome completo corretto")

    # Campi person (se collegato)
    person_first_name: Optional[str] = Field(None, description="Nome persona")
    person_last_name: Optional[str] = Field(None, description="Cognome persona")
    person_email: Optional[str] = Field(None, description="Email persona")
    person_phone: Optional[str] = Field(None, description="Telefono persona")

    reason: str = Field(..., description="Motivazione della rettifica richiesta")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "nuovo.email@example.com",
                "full_name": "Mario Rossi",
                "reason": "Correzione indirizzo email errato"
            }
        }


class GDPRRectificationResponse(BaseModel):
    """Response per rettifica dati"""
    success: bool
    message: str
    updated_fields: List[str]
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# GDPR Art. 17 - Right to Erasure (Cancellazione / "Right to be Forgotten")
# ============================================================================

class GDPRErasureRequest(BaseModel):
    """Request per cancellazione account (GDPR Art. 17)"""
    reason: str = Field(..., description="Motivazione richiesta cancellazione (obbligatorio per compliance)")
    confirm_deletion: bool = Field(..., description="Conferma esplicita cancellazione (deve essere True)")

    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Non utilizzo più il servizio",
                "confirm_deletion": True
            }
        }


class GDPRErasureResponse(BaseModel):
    """Response per cancellazione account"""
    success: bool
    message: str
    user_id: int
    anonymized: bool
    deleted_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# GDPR Art. 18 - Right to Restriction (Limitazione Trattamento)
# ============================================================================

class GDPRRestrictionRequest(BaseModel):
    """Request per limitazione trattamento dati (GDPR Art. 18)"""
    reason: str = Field(..., description="Motivazione richiesta limitazione")
    restriction_type: str = Field(..., description="Tipo limitazione: 'temporary' o 'permanent'")

    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Contestazione accuratezza dati in corso",
                "restriction_type": "temporary"
            }
        }


class GDPRRestrictionResponse(BaseModel):
    """Response per limitazione trattamento"""
    success: bool
    message: str
    user_id: int
    restriction_active: bool
    restriction_type: str
    restricted_at: datetime

    class Config:
        from_attributes = True

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, rate_limit_gdpr
from app.models.user import User
from app.services.gdpr_service import GDPRService
from app.schemas.gdpr import (
    GDPRMyDataResponse,
    GDPRPortabilityResponse,
    GDPRRectificationRequest,
    GDPRRectificationResponse,
    GDPRErasureRequest,
    GDPRErasureResponse,
    GDPRRestrictionRequest,
    GDPRRestrictionResponse
)


router = APIRouter(prefix="/gdpr", tags=["GDPR Rights"])

logger = logging.getLogger(__name__)


# ============================================================================
# GDPR Art. 15 - Right of Access (Diritto di Accesso)
# ============================================================================

@router.get("/my-data", response_model=GDPRMyDataResponse)
async def get_my_data(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(rate_limit_gdpr),
):
    """
    **GDPR Art. 15 - Diritto di Accesso ai Dati Personali**
    
    Restituisce un export completo di tutti i dati personali dell'utente autenticato,
    inclusi:
    - Dati account (username, email, ruolo)
    - Dati anagrafici (person)
    - Asset assegnati
    - Storico assegnazioni
    - SIM e badge assegnati
    - Audit logs (ultime 100 azioni)
    
    **Compliance:**
    - GDPR Art. 15: Diritto dell'interessato di ottenere conferma che sia o meno in corso
      un trattamento di dati personali che lo riguardano
    - Risposta entro 30 giorni dalla richiesta (automatica via API)
    - Tracciamento richiesta in audit_logs (evento GDPR_ACCESS)
    
    **Accessibilità:** User, Operatore, Admin (solo propri dati)
    """
    try:
        data = GDPRService.get_user_data(db, current_user.id)
        return data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante export dati: {str(e)}")


# ============================================================================
# GDPR Art. 20 - Right to Data Portability (Portabilità)
# ============================================================================

@router.get("/data-portability", response_model=GDPRPortabilityResponse)
async def get_data_portability(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(rate_limit_gdpr),
):
    """
    **GDPR Art. 20 - Diritto alla Portabilità dei Dati**
    
    Restituisce i dati personali in formato strutturato, machine-readable (JSON),
    per consentire il trasferimento ad altro titolare del trattamento.
    
    **Formato export:**
    - JSON strutturato per interoperabilità
    - Tutti i dati forniti dall'utente
    - Dati derivati dalle attività dell'utente
    
    **Compliance:**
    - GDPR Art. 20: Diritto di ricevere i dati in formato strutturato, di uso comune
      e leggibile da dispositivo automatico
    - Possibilità di trasmettere dati direttamente ad altro titolare (se tecnicamente fattibile)
    - Tracciamento richiesta in audit_logs (evento GDPR_PORTABILITY)
    
    **Accessibilità:** User, Operatore, Admin (solo propri dati)
    """
    try:
        data = GDPRService.export_portability(db, current_user.id)
        return data
    except ValueError as e:
        logger.warning("GDPR data-portability: %s", e)
        raise HTTPException(status_code=404, detail="Risorsa non trovata")
    except Exception as e:
        logger.error("GDPR operation failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# GDPR Art. 16 - Right to Rectification (Rettifica)
# ============================================================================

@router.put("/rectification", response_model=GDPRRectificationResponse)
async def rectify_data(
    rectification: GDPRRectificationRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(rate_limit_gdpr),
):
    """
    **GDPR Art. 16 - Diritto di Rettifica**
    
    Permette all'utente di correggere dati personali inesatti o incompleti.
    
    **Campi rettificabili:**
    - User: email, full_name
    - Person: first_name, last_name, email, phone
    
    **Compliance:**
    - GDPR Art. 16: L'interessato ha il diritto di ottenere la rettifica dei dati
      personali inesatti che lo riguardano
    - Risposta senza ingiustificato ritardo
    - Motivazione obbligatoria (campo "reason")
    - Tracciamento richiesta in audit_logs (evento GDPR_RECTIFICATION)
    
    **Accessibilità:** User, Operatore, Admin (solo propri dati)
    """
    try:
        response = GDPRService.rectify_data(db, current_user.id, rectification)
        return response
    except ValueError as e:
        logger.warning("GDPR rectification: %s", e)
        raise HTTPException(status_code=400, detail="Richiesta non valida")
    except Exception as e:
        logger.error("GDPR operation failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# GDPR Art. 17 - Right to Erasure (Cancellazione / "Right to be Forgotten")
# ============================================================================

@router.delete("/erasure", response_model=GDPRErasureResponse)
async def erase_user_data(
    erasure: GDPRErasureRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(rate_limit_gdpr),
):
    """
    **GDPR Art. 17 - Diritto alla Cancellazione ("Right to be Forgotten")**
    
    Permette all'utente di richiedere la cancellazione del proprio account e dati personali.
    
    **Implementazione:**
    - **Anonimizzazione** invece di cancellazione fisica (per compliance audit)
    - Username → "deleted_user_{id}"
    - Email → "deleted_{id}@anonymized.local"
    - Password → "DELETED"
    - Account disabilitato (is_active=False)
    - Person scollegata e anonimizzata
    - **Audit logs mantenuti** per tracciabilità legale (obbligo normativo ISO 27001)
    
    **Eccezioni (dati NON cancellabili per legge):**
    - Audit logs (obbligo conservazione per tracciabilità)
    - Dati contabili/fiscali (obbligo conservazione 10 anni)
    
    **Compliance:**
    - GDPR Art. 17: Diritto alla cancellazione senza ingiustificato ritardo
    - Conferma esplicita richiesta (confirm_deletion=True)
    - Motivazione obbligatoria
    - Tracciamento richiesta in audit_logs (evento GDPR_ERASURE)
    
    **ATTENZIONE:** Azione IRREVERSIBILE
    
    **Accessibilità:** User, Operatore, Admin (solo propri dati)
    """
    try:
        response = GDPRService.erase_user_data(db, current_user.id, erasure)
        return response
    except ValueError as e:
        logger.warning("GDPR erasure: %s", e)
        raise HTTPException(status_code=400, detail="Richiesta non valida")
    except Exception as e:
        logger.error("GDPR operation failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# GDPR Art. 18 - Right to Restriction (Limitazione Trattamento)
# ============================================================================

@router.post("/restriction", response_model=GDPRRestrictionResponse)
async def restrict_processing(
    restriction: GDPRRestrictionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(rate_limit_gdpr),
):
    """
    **GDPR Art. 18 - Diritto di Limitazione del Trattamento**
    
    Permette all'utente di limitare il trattamento dei propri dati personali.
    
    **Implementazione:**
    - Account disabilitato (is_active=False)
    - Dati conservati ma non più utilizzabili per operazioni attive
    - Tipi limitazione:
      - **temporary**: limitazione temporanea (es. contestazione accuratezza dati)
      - **permanent**: limitazione permanente
    
    **Casi d'uso GDPR Art. 18:**
    1. Contestazione accuratezza dati (in attesa verifica)
    2. Trattamento illecito (utente non vuole cancellazione ma limitazione)
    3. Dati non più necessari ma utente li richiede per accertamento/difesa diritti
    4. Opposizione al trattamento (in attesa verifica prevalenza motivi legittimi)
    
    **Compliance:**
    - GDPR Art. 18: Diritto di ottenere limitazione del trattamento
    - Motivazione obbligatoria
    - Tracciamento richiesta in audit_logs (evento GDPR_RESTRICTION)
    
    **Accessibilità:** User, Operatore, Admin (solo propri dati)
    """
    try:
        response = GDPRService.restrict_processing(db, current_user.id, restriction)
        return response
    except ValueError as e:
        logger.warning("GDPR restriction: %s", e)
        raise HTTPException(status_code=400, detail="Richiesta non valida")
    except Exception as e:
        logger.error("GDPR operation failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")

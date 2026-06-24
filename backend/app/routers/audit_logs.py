from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime


from app.api.deps import get_db, get_current_active_admin
from app.models.user import User
from app.schemas.audit_log import AuditLogOut, AuditLogListResponse
from app.services.audit_service import AuditService


router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("/", response_model=AuditLogListResponse)
def list_audit_logs(
    skip: int = Query(0, ge=0, description="Numero di record da saltare"),
    limit: int = Query(100, ge=1, le=500, description="Numero massimo di record"),
    action: Optional[str] = Query(None, description="Filtra per azione"),
    entity_type: Optional[str] = Query(None, description="Filtra per tipo entità"),
    entity_id: Optional[int] = Query(None, description="Filtra per ID entità"),
    user_id: Optional[int] = Query(None, description="Filtra per ID utente"),
    username: Optional[str] = Query(None, description="Filtra per username"),
    date_from: Optional[datetime] = Query(None, description="Data inizio (ISO 8601)"),
    date_to: Optional[datetime] = Query(None, description="Data fine (ISO 8601)"),
    search: Optional[str] = Query(None, description="Ricerca testuale"),
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Recupera la lista dei log di audit con filtri opzionali.

    **Richiede ruolo Admin.**

    Filtri disponibili:
    - action: CREATE, UPDATE, DELETE, LOGIN, LOGOUT, etc.
    - entity_type: asset, person, user, sim, badge, etc.
    - entity_id: ID specifico dell'entità
    - user_id: ID dell'utente che ha eseguito l'azione
    - username: Username (ricerca parziale case-insensitive)
    - date_from/date_to: Range temporale
    - search: Ricerca testuale in details, username, action
    """
    logs, total = AuditService.get_logs(
        db=db,
        skip=skip,
        limit=limit,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        username=username,
        date_from=date_from,
        date_to=date_to,
        search=search
    )

    return AuditLogListResponse(
        items=logs,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/entity/{entity_type}/{entity_id}", response_model=list[AuditLogOut])
def get_entity_history(
    entity_type: str,
    entity_id: int,
    limit: int = Query(50, ge=1, le=200, description="Numero massimo di record"),
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Recupera la storia completa di un'entità specifica.

    **Richiede ruolo Admin.**

    Restituisce tutti i log relativi a una specifica entità ordinati per data decrescente.
    """
    logs = AuditService.get_entity_history(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit
    )

    return logs


@router.get("/user/{user_id}/activity", response_model=list[AuditLogOut])
def get_user_activity(
    user_id: int,
    limit: int = Query(100, ge=1, le=500, description="Numero massimo di record"),
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Recupera l'attività recente di un utente specifico.

    **Richiede ruolo Admin.**

    Restituisce tutti i log delle azioni eseguite dall'utente ordinati per data decrescente.
    """
    logs = AuditService.get_user_activity(
        db=db,
        user_id=user_id,
        limit=limit
    )

    return logs


@router.delete("/rotate")
def rotate_audit_logs(
    retention_months: int = Query(24, ge=1, le=120, description="Mesi di retention"),
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Archivia ed elimina audit logs oltre il periodo di retention. Richiede ruolo Admin.
    I log vengono salvati in formato JSON prima dell'eliminazione.
    """
    result = AuditService.rotate_logs(db=db, retention_months=retention_months)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

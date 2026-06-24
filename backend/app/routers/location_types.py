from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.location import (
    LocationTypeCreate,
    LocationTypeListResponse,
    LocationTypeResponse,
    LocationTypeUpdate,
)
from app.services.audit_service import AuditService
from app.services.location_service import (
    create_location_type,
    delete_location_type,
    get_location_type,
    get_location_types,
    update_location_type,
)

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/location-types", tags=["Location Types"])


@router.get("", response_model=LocationTypeListResponse)
def list_location_types(
    skip: int = Query(0, ge=0, description="Numero di record da saltare"),
    limit: int = Query(100, ge=1, le=1000, description="Numero massimo di record"),
    is_active: Optional[bool] = Query(None, description="Filtra per stato attivo"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recupera la lista dei tipi di locazione con paginazione e filtri."""
    return get_location_types(db=db, skip=skip, limit=limit, is_active=is_active)


@router.get("/{id}", response_model=LocationTypeResponse)
def get_location_type_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recupera un tipo di locazione per ID."""
    result = get_location_type(db=db, location_type_id=id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo di locazione con ID {id} non trovato",
        )
    return result


@router.post("", response_model=LocationTypeResponse, status_code=status.HTTP_201_CREATED)
def create_location_type_endpoint(
    data: LocationTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crea un nuovo tipo di locazione."""
    if current_user.role not in ["admin", "operatore"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permesso di creare tipi di locazione",
        )
    result = create_location_type(db=db, data=data)
    try:
        AuditService.log_action(
            db=db,
            action="CREATE",
            entity_type="location_type",
            entity_id=result.id,
            user_id=current_user.id,
            username=current_user.username,
            details=f"Creato tipo di locazione '{result.name}'",
            new_value={"name": result.name, "icon": result.icon},
        )
    except Exception as e:
        logger.warning("Audit log failed: %s", e)
    return result


@router.put("/{id}", response_model=LocationTypeResponse)
def update_location_type_endpoint(
    id: int,
    data: LocationTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggiorna un tipo di locazione esistente."""
    if current_user.role not in ["admin", "operatore"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permesso di modificare tipi di locazione",
        )
    result = update_location_type(db=db, location_type_id=id, data=data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo di locazione con ID {id} non trovato",
        )
    try:
        AuditService.log_action(
            db=db,
            action="UPDATE",
            entity_type="location_type",
            entity_id=id,
            user_id=current_user.id,
            username=current_user.username,
            details=f"Aggiornato tipo di locazione '{result.name}'",
            new_value={"name": result.name, "icon": result.icon},
        )
    except Exception as e:
        logger.warning("Audit log failed: %s", e)
    return result


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location_type_endpoint(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Disattiva un tipo di locazione (soft delete)."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo gli amministratori possono disattivare tipi di locazione",
        )
    success = delete_location_type(db=db, location_type_id=id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo di locazione con ID {id} non trovato",
        )
    try:
        AuditService.log_action(
            db=db,
            action="DELETE",
            entity_type="location_type",
            entity_id=id,
            user_id=current_user.id,
            username=current_user.username,
            details=f"Disattivato tipo di locazione con ID {id}",
        )
    except Exception as e:
        logger.warning("Audit log failed: %s", e)

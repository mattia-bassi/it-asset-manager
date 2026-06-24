from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.location import (
    LocationCreate,
    LocationListResponse,
    LocationResponse,
    LocationUpdate,
)
from app.services.audit_service import AuditService
from app.services.location_service import (
    create_location,
    delete_location,
    get_location,
    get_locations,
    update_location,
)

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/locations", tags=["Locations"])


@router.get("", response_model=LocationListResponse)
def list_locations(
    skip: int = Query(0, ge=0, description="Numero di record da saltare"),
    limit: int = Query(100, ge=1, le=1000, description="Numero massimo di record"),
    site_id: Optional[int] = Query(None, description="Filtra per sede"),
    location_type_id: Optional[int] = Query(None, description="Filtra per tipo di locazione"),
    is_active: Optional[bool] = Query(None, description="Filtra per stato attivo"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recupera la lista delle locazioni con paginazione e filtri."""
    return get_locations(
        db=db,
        skip=skip,
        limit=limit,
        site_id=site_id,
        location_type_id=location_type_id,
        is_active=is_active,
    )


@router.get("/{id}", response_model=LocationResponse)
def get_location_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recupera una locazione per ID."""
    result = get_location(db=db, location_id=id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Locazione con ID {id} non trovata",
        )
    return result


@router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def create_location_endpoint(
    data: LocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crea una nuova locazione."""
    if current_user.role not in ["admin", "operatore"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permesso di creare locazioni",
        )
    result = create_location(db=db, data=data)
    try:
        AuditService.log_action(
            db=db,
            action="CREATE",
            entity_type="location",
            entity_id=result.id,
            user_id=current_user.id,
            username=current_user.username,
            details=f"Creata locazione '{result.name}'",
            new_value={"name": result.name, "site_id": result.site_id, "location_type_id": result.location_type_id},
        )
    except Exception as e:
        logger.warning("Audit log failed: %s", e)
    return result


@router.put("/{id}", response_model=LocationResponse)
def update_location_endpoint(
    id: int,
    data: LocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggiorna una locazione esistente."""
    if current_user.role not in ["admin", "operatore"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permesso di modificare locazioni",
        )
    result = update_location(db=db, location_id=id, data=data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Locazione con ID {id} non trovata",
        )
    try:
        AuditService.log_action(
            db=db,
            action="UPDATE",
            entity_type="location",
            entity_id=id,
            user_id=current_user.id,
            username=current_user.username,
            details=f"Aggiornata locazione '{result.name}'",
            new_value={"name": result.name, "site_id": result.site_id, "location_type_id": result.location_type_id},
        )
    except Exception as e:
        logger.warning("Audit log failed: %s", e)
    return result


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location_endpoint(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Disattiva una locazione (soft delete)."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo gli amministratori possono disattivare locazioni",
        )
    success = delete_location(db=db, location_id=id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Locazione con ID {id} non trovata",
        )
    try:
        AuditService.log_action(
            db=db,
            action="DELETE",
            entity_type="location",
            entity_id=id,
            user_id=current_user.id,
            username=current_user.username,
            details=f"Disattivata locazione con ID {id}",
        )
    except Exception as e:
        logger.warning("Audit log failed: %s", e)

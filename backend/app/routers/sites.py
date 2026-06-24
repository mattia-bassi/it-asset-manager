from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from app.api.deps import get_db, get_current_user, get_current_active_admin
from app.schemas.site import Site, SiteCreate, SiteUpdate, SiteList
from app.services.site_service import SiteService
from app.models.user import User
import math

router = APIRouter(prefix="/sites", tags=["Sites"])


@router.get("", response_model=SiteList)
def get_sites(
    skip: int = Query(0, ge=0, description="Numero di record da saltare"),
    limit: int = Query(100, ge=1, le=1000, description="Numero massimo di record"),
    is_active: Optional[bool] = Query(None, description="Filtra per stato attivo"),
    search: Optional[str] = Query(None, description="Ricerca per nome o città"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recupera la lista delle sedi con paginazione e filtri."""
    sites, total = SiteService.get_all(
        db=db,
        skip=skip,
        limit=limit,
        is_active=is_active,
        search=search
    )
    
    return {
        "items": sites,
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "page_size": limit,
        "pages": math.ceil(total / limit) if limit > 0 else 1
    }


@router.get("/{site_id}", response_model=Site)
def get_site(site_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Recupera una sede per ID."""
    site = SiteService.get_by_id(db, site_id)
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sede con ID {site_id} non trovata"
        )
    return site


@router.post("", response_model=Site, status_code=status.HTTP_201_CREATED)
def create_site(site_data: SiteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Crea una nuova sede."""
    try:
        site = SiteService.create(db, site_data)
        return site
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{site_id}", response_model=Site)
def update_site(
    site_id: int,
    site_data: SiteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aggiorna una sede esistente."""
    try:
        site = SiteService.update(db, site_id, site_data)
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sede con ID {site_id} non trovata"
            )
        return site
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_site(site_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Disattiva una sede (soft delete)."""
    success = SiteService.delete(db, site_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sede con ID {site_id} non trovata"
        )


@router.delete("/{site_id}/hard", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_site(site_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_admin)):
    """Elimina definitivamente una sede dal database."""
    success = SiteService.hard_delete(db, site_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sede con ID {site_id} non trovata"
        )


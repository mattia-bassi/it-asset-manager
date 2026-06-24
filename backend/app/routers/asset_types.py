from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from app.api.deps import get_db, get_current_user
from app.schemas.asset_type import AssetType, AssetTypeCreate, AssetTypeUpdate, AssetTypeList
from app.services.asset_type_service import AssetTypeService
from app.models.user import User
import math

router = APIRouter(prefix="/asset-types", tags=["Asset Types"])


@router.get("", response_model=AssetTypeList)
def get_asset_types(
    skip: int = Query(0, ge=0, description="Numero di record da saltare"),
    limit: int = Query(100, ge=1, le=1000, description="Numero massimo di record"),
    is_active: Optional[bool] = Query(None, description="Filtra per stato attivo"),
    parent_id: Optional[int] = Query(None, description="Filtra per tipo padre"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recupera la lista dei tipi di asset con paginazione e filtri."""
    types, total = AssetTypeService.get_all(
        db=db,
        skip=skip,
        limit=limit,
        is_active=is_active,
        parent_id=parent_id
    )
    
    return {
        "items": types,
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "page_size": limit,
        "pages": math.ceil(total / limit) if limit > 0 else 1
    }


@router.get("/hierarchy", response_model=list[dict])
def get_asset_types_hierarchy(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Recupera la gerarchia completa dei tipi in formato ad albero."""
    return AssetTypeService.get_hierarchy(db)


@router.get("/{type_id}", response_model=AssetType)
def get_asset_type(type_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Recupera un tipo per ID."""
    asset_type = AssetTypeService.get_by_id(db, type_id)
    if not asset_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo con ID {type_id} non trovato"
        )
    return asset_type


@router.post("", response_model=AssetType, status_code=status.HTTP_201_CREATED)
def create_asset_type(type_data: AssetTypeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Crea un nuovo tipo di asset."""
    asset_type = AssetTypeService.create(db, type_data)
    return asset_type


@router.put("/{type_id}", response_model=AssetType)
def update_asset_type(
    type_id: int,
    type_data: AssetTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aggiorna un tipo esistente."""
    asset_type = AssetTypeService.update(db, type_id, type_data)
    if not asset_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo con ID {type_id} non trovato"
        )
    return asset_type


@router.delete("/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset_type(type_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Disattiva un tipo (soft delete)."""
    success = AssetTypeService.delete(db, type_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo con ID {type_id} non trovato"
        )


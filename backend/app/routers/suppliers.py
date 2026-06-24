from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.supplier import SupplierCreate, SupplierListResponse, SupplierResponse, SupplierUpdate
from app.services.supplier_service import SupplierService

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.get("", response_model=SupplierListResponse)
def list_suppliers(
    skip: int = Query(0, ge=0, description="Numero di record da saltare"),
    limit: int = Query(100, ge=1, le=1000, description="Numero massimo di record"),
    search: Optional[str] = Query(None, description="Ricerca per nome fornitore"),
    is_active: Optional[bool] = Query(None, description="Filtra per stato attivo"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recupera la lista dei fornitori con paginazione e filtri."""
    return SupplierService.get_all(db=db, skip=skip, limit=limit, search=search, is_active=is_active)


@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(
    data: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crea un nuovo fornitore."""
    if current_user.role not in ["admin", "operatore"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo Admin e Operatore possono creare fornitori",
        )
    return SupplierService.create(db=db, data=data, current_user=current_user)


@router.get("/{id}", response_model=SupplierResponse)
def get_supplier(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recupera un fornitore per ID."""
    supplier = SupplierService.get_by_id(db=db, supplier_id=id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fornitore con ID {id} non trovato",
        )
    return supplier


@router.put("/{id}", response_model=SupplierResponse)
def update_supplier(
    id: int,
    data: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggiorna un fornitore esistente."""
    if current_user.role not in ["admin", "operatore"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo Admin e Operatore possono modificare fornitori",
        )
    try:
        return SupplierService.update(db=db, supplier_id=id, data=data, current_user=current_user)
    except HTTPException:
        raise


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Disattiva un fornitore (soft delete)."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo gli Admin possono disattivare fornitori",
        )
    try:
        SupplierService.delete(db=db, supplier_id=id, current_user=current_user)
    except HTTPException:
        raise


@router.get("/{id}/assets")
def get_supplier_assets(
    id: int,
    skip: int = Query(0, ge=0, description="Numero di record da saltare"),
    limit: int = Query(100, ge=1, le=1000, description="Numero massimo di record"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recupera gli asset collegati a un fornitore."""
    try:
        return SupplierService.get_assets(db=db, supplier_id=id, skip=skip, limit=limit)
    except HTTPException:
        raise

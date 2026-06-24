from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from app.api.deps import get_db, get_current_user
from app.schemas.inventory_sku import InventorySku, InventorySkuCreate, InventorySkuUpdate, InventorySkuList, InventorySkuQuantityUpdate
from app.services.inventory_sku_service import InventorySkuService
import math
from app.models.user import User

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("", response_model=InventorySkuList)
def get_inventory(
    skip: int = Query(0, ge=0, description="Numero di record da saltare"),
    limit: int = Query(100, ge=1, le=1000, description="Numero massimo di record"),
    is_active: Optional[bool] = Query(None, description="Filtra per stato attivo"),
    category: Optional[str] = Query(None, description="Filtra per categoria"),
    low_stock_only: bool = Query(False, description="Solo materiali sotto soglia"),
    search: Optional[str] = Query(None, description="Ricerca per dispositivo, marca o categoria"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recupera la lista dei materiali di magazzino con paginazione e filtri."""
    # Solo admin e operatori possono accedere al magazzino
    if current_user.role == "user":
        return InventorySkuList(items=[], total=0, page=1, page_size=limit, pages=0, low_stock_count=0)
    skus, total, low_stock_count = InventorySkuService.get_all(
        db=db,
        skip=skip,
        limit=limit,
        is_active=is_active,
        category=category,
        low_stock_only=low_stock_only,
        search=search
    )
    
    return {
        "items": skus,
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "page_size": limit,
        "pages": math.ceil(total / limit) if limit > 0 else 1,
        "low_stock_count": low_stock_count
    }


@router.get("/categories", response_model=list[str])
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recupera tutte le categorie distinte."""
    # Solo admin e operatori possono vedere categorie magazzino
    if current_user.role == "user":
        return []
    return InventorySkuService.get_categories(db)


@router.get("/{sku_id}", response_model=InventorySku)
def get_inventory_item(
    sku_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recupera un materiale per ID."""
    # Solo admin e operatori possono vedere item magazzino
    if current_user.role == "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai accesso al magazzino"
        )
    sku = InventorySkuService.get_by_id(db, sku_id)
    if not sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Materiale con ID {sku_id} non trovato"
        )
    return sku


@router.post("", response_model=InventorySku, status_code=status.HTTP_201_CREATED)
def create_inventory_item(
    sku_data: InventorySkuCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crea un nuovo materiale di magazzino."""
    # Solo admin e operatori possono creare item magazzino
    if current_user.role == "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permessi per creare item magazzino"
        )
    sku = InventorySkuService.create(db, sku_data)
    return sku


@router.put("/{sku_id}", response_model=InventorySku)
def update_inventory_item(
    sku_id: int,
    sku_data: InventorySkuUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggiorna un materiale esistente."""
    # Solo admin e operatori possono modificare magazzino
    if current_user.role == "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permessi per modificare magazzino"
        )
    sku = InventorySkuService.update(db, sku_id, sku_data)
    if not sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Materiale con ID {sku_id} non trovato"
        )
    return sku


@router.patch("/{sku_id}/quantity", response_model=InventorySku)
def update_quantity(
    sku_id: int,
    quantity_data: InventorySkuQuantityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggiorna solo la quantità di un materiale."""
    # Solo admin e operatori possono aggiornare quantità
    if current_user.role == "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permessi per modificare quantità"
        )
    sku = InventorySkuService.update_quantity(db, sku_id, quantity_data)
    if not sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Materiale con ID {sku_id} non trovato"
        )
    return sku


@router.patch("/{sku_id}/adjust", response_model=InventorySku)
def adjust_quantity(
    sku_id: int,
    adjustment: int = Query(..., description="Aggiustamento quantità (positivo=carico, negativo=scarico)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggiusta la quantità (carico/scarico)."""
    # Solo admin e operatori possono regolare quantità
    if current_user.role == "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permessi per regolare quantità"
        )
    try:
        sku = InventorySkuService.adjust_quantity(db, sku_id, adjustment)
        if not sku:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Materiale con ID {sku_id} non trovato"
            )
        return sku
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{sku_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory_item(
    sku_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Disattiva un materiale (soft delete)."""
    # Solo admin e operatori possono eliminare item
    if current_user.role == "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permessi per eliminare item magazzino"
        )
    success = InventorySkuService.delete(db, sku_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Materiale con ID {sku_id} non trovato"
        )


@router.delete("/{sku_id}/hard", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_inventory_item(
    sku_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Elimina definitivamente un materiale dal database."""
    # Solo admin può eliminare permanentemente
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo gli amministratori possono eliminare permanentemente item"
        )
    success = InventorySkuService.hard_delete(db, sku_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Materiale con ID {sku_id} non trovato"
        )


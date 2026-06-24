from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from app.models.inventory_sku import InventorySku
from app.schemas.inventory_sku import InventorySkuCreate, InventorySkuUpdate, InventorySkuQuantityUpdate


class InventorySkuService:
    """Service per la gestione del magazzino."""

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        category: Optional[str] = None,
        low_stock_only: bool = False,
        search: Optional[str] = None
    ) -> tuple[list[InventorySku], int, int]:
        """
        Recupera tutti i materiali con filtri opzionali.
        Ritorna (lista_materiali, totale, conteggio_sotto_soglia)
        """
        query = select(InventorySku)
        
        # Filtro attivo/inattivo
        if is_active is not None:
            query = query.where(InventorySku.is_active == is_active)
        
        # Filtro per categoria
        if category:
            query = query.where(InventorySku.category == category)
        
        # Filtro solo materiali sotto soglia
        if low_stock_only:
            query = query.where(InventorySku.quantity <= InventorySku.min_quantity)
        
        # Ricerca per device o brand
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    InventorySku.device.ilike(search_term),
                    InventorySku.brand.ilike(search_term),
                    InventorySku.category.ilike(search_term)
                )
            )
        
        # Conta totale (prima di paginazione)
        total = db.scalar(select(func.count()).select_from(query.subquery()))
        
        # Conta materiali sotto soglia
        low_stock_count = db.scalar(
            select(func.count()).select_from(InventorySku).where(
                InventorySku.quantity <= InventorySku.min_quantity,
                InventorySku.is_active == True
            )
        )
        
        # Paginazione e ordinamento
        query = query.order_by(InventorySku.category, InventorySku.device).offset(skip).limit(limit)
        skus = db.scalars(query).all()
        
        return list(skus), total or 0, low_stock_count or 0

    @staticmethod
    def get_by_id(db: Session, sku_id: int) -> Optional[InventorySku]:
        """Recupera un materiale per ID."""
        return db.scalar(select(InventorySku).where(InventorySku.id == sku_id))

    @staticmethod
    def get_categories(db: Session) -> list[str]:
        """Recupera tutte le categorie distinte."""
        categories = db.scalars(
            select(InventorySku.category).distinct().where(InventorySku.is_active == True).order_by(InventorySku.category)
        ).all()
        return list(categories)

    @staticmethod
    def create(db: Session, sku_data: InventorySkuCreate) -> InventorySku:
        """Crea un nuovo materiale."""
        sku = InventorySku(**sku_data.model_dump())
        db.add(sku)
        db.commit()
        db.refresh(sku)
        return sku

    @staticmethod
    def update(db: Session, sku_id: int, sku_data: InventorySkuUpdate) -> Optional[InventorySku]:
        """Aggiorna un materiale esistente."""
        sku = InventorySkuService.get_by_id(db, sku_id)
        if not sku:
            return None
        
        update_data = sku_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(sku, field, value)
        
        db.commit()
        db.refresh(sku)
        return sku

    @staticmethod
    def update_quantity(db: Session, sku_id: int, quantity_data: InventorySkuQuantityUpdate) -> Optional[InventorySku]:
        """Aggiorna solo la quantità di un materiale."""
        sku = InventorySkuService.get_by_id(db, sku_id)
        if not sku:
            return None
        
        sku.quantity = quantity_data.quantity
        db.commit()
        db.refresh(sku)
        return sku

    @staticmethod
    def adjust_quantity(db: Session, sku_id: int, adjustment: int) -> Optional[InventorySku]:
        """
        Aggiusta la quantità (positivo per carico, negativo per scarico).
        Ritorna None se il materiale non esiste o se l'operazione porterebbe a quantità negativa.
        """
        sku = InventorySkuService.get_by_id(db, sku_id)
        if not sku:
            return None
        
        new_quantity = sku.quantity + adjustment
        if new_quantity < 0:
            raise ValueError("La quantità risultante non può essere negativa")
        
        sku.quantity = new_quantity
        db.commit()
        db.refresh(sku)
        return sku

    @staticmethod
    def delete(db: Session, sku_id: int) -> bool:
        """Disattiva un materiale (soft delete)."""
        sku = InventorySkuService.get_by_id(db, sku_id)
        if not sku:
            return False
        
        sku.is_active = False
        db.commit()
        return True

    @staticmethod
    def hard_delete(db: Session, sku_id: int) -> bool:
        """Elimina definitivamente un materiale dal database."""
        sku = InventorySkuService.get_by_id(db, sku_id)
        if not sku:
            return False
        
        db.delete(sku)
        db.commit()
        return True


import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierListResponse, SupplierResponse
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class SupplierService:
    """Service per la gestione dei fornitori."""

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> SupplierListResponse:
        """
        Recupera tutti i fornitori con filtri opzionali.
        Ritorna SupplierListResponse con items e total.
        """
        query = select(Supplier)

        if search:
            search_term = f"%{search}%"
            query = query.where(Supplier.name.ilike(search_term))

        if is_active is not None:
            query = query.where(Supplier.is_active == is_active)

        total = db.scalar(select(func.count()).select_from(query.subquery()))

        query = query.order_by(Supplier.name.asc()).offset(skip).limit(limit)
        results = db.execute(query).scalars().all()

        items = [SupplierResponse.model_validate(s) for s in results]
        return SupplierListResponse(items=items, total=total or 0)

    @staticmethod
    def get_by_id(db: Session, supplier_id: int) -> Optional[Supplier]:
        """Recupera un fornitore per ID."""
        return db.scalar(select(Supplier).where(Supplier.id == supplier_id))

    @staticmethod
    def create(db: Session, data: SupplierCreate, current_user) -> Supplier:
        """Crea un nuovo fornitore."""
        supplier = Supplier(**data.model_dump())
        db.add(supplier)
        db.commit()
        db.refresh(supplier)

        try:
            AuditService.log_action(
                db=db,
                action="CREATE",
                entity_type="suppliers",
                entity_id=supplier.id,
                details=f"Creato fornitore {supplier.name}",
                new_value={"name": supplier.name, "email": supplier.email},
                user_id=getattr(current_user, "id", None),
                username=getattr(current_user, "username", None),
            )
        except Exception as e:
            logger.error("Audit log failed: %s", e)

        return supplier

    @staticmethod
    def update(db: Session, supplier_id: int, data: SupplierUpdate, current_user) -> Supplier:
        """Aggiorna un fornitore esistente."""
        supplier = SupplierService.get_by_id(db, supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail=f"Fornitore con ID {supplier_id} non trovato")

        old_value = {
            "name": supplier.name,
            "email": supplier.email,
            "is_active": supplier.is_active,
        }

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(supplier, field, value)

        db.commit()
        db.refresh(supplier)

        try:
            AuditService.log_action(
                db=db,
                action="UPDATE",
                entity_type="suppliers",
                entity_id=supplier.id,
                details=f"Aggiornato fornitore {supplier.name}",
                old_value=old_value,
                new_value={"name": supplier.name, "email": supplier.email, "is_active": supplier.is_active},
                user_id=getattr(current_user, "id", None),
                username=getattr(current_user, "username", None),
            )
        except Exception as e:
            logger.error("Audit log failed: %s", e)

        return supplier

    @staticmethod
    def delete(db: Session, supplier_id: int, current_user) -> dict:
        """Disattiva un fornitore (soft delete: is_active=False)."""
        supplier = SupplierService.get_by_id(db, supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail=f"Fornitore con ID {supplier_id} non trovato")

        active_assets_count = db.scalar(
            select(func.count()).select_from(Asset).where(
                Asset.supplier_id == supplier_id,
                Asset.is_active.is_(True),
            )
        ) or 0
        if active_assets_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Impossibile eliminare: ci sono {active_assets_count} asset attivi collegati a questo fornitore.",
            )

        supplier.is_active = False
        db.commit()

        try:
            AuditService.log_action(
                db=db,
                action="DELETE",
                entity_type="suppliers",
                entity_id=supplier.id,
                details=f"Fornitore disattivato (soft delete): {supplier.name}",
                old_value={"is_active": True, "name": supplier.name},
                user_id=getattr(current_user, "id", None),
                username=getattr(current_user, "username", None),
            )
        except Exception as e:
            logger.error("Audit log failed: %s", e)

        return {"message": "Fornitore disattivato con successo"}

    @staticmethod
    def get_assets(db: Session, supplier_id: int, skip: int = 0, limit: int = 100) -> dict:
        """Ritorna gli asset collegati a questo fornitore."""
        supplier = SupplierService.get_by_id(db, supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail=f"Fornitore con ID {supplier_id} non trovato")

        count_query = select(func.count()).select_from(Asset).where(Asset.supplier_id == supplier_id)
        total = db.scalar(count_query) or 0

        assets_query = (
            select(Asset)
            .where(Asset.supplier_id == supplier_id)
            .order_by(Asset.manufacturer, Asset.model)
            .offset(skip)
            .limit(limit)
        )
        assets = db.execute(assets_query).scalars().all()

        items = [
            {
                "id": a.id,
                "asset_code": a.asset_code,
                "serial_number": a.serial_number,
                "manufacturer": a.manufacturer,
                "model": a.model,
                "status": a.status,
                "is_active": a.is_active,
            }
            for a in assets
        ]

        return {"items": items, "total": total}

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.api.deps import get_db, get_current_user
from app.models.asset import Asset
from app.models.assignment import Assignment
from app.models.inventory_sku import InventorySku
from app.models.sim import Sim
from app.models.asset_type import AssetType
from app.models.person import Person
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app.models.user import User

import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Dashboard"])


@router.get("/overview")
def get_overview_stats(
    days: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[str] = None,
    asset_type_id: Optional[int] = None,
    assignment_type: Optional[str] = None,
    alerts_only: Optional[bool] = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Contatori generali per la dashboard con filtri."""
    try:
        # Calcola date filter
        date_filter_start = None
        date_filter_end = datetime.now()

        if days:
            date_filter_start = datetime.now() - timedelta(days=int(days))
        elif date_from:
            date_filter_start = datetime.fromisoformat(date_from.replace("Z", "+00:00"))

        if date_to:
            date_filter_end = datetime.fromisoformat(date_to.replace("Z", "+00:00"))

        # Role-based filter
        person_id_filter = None
        if current_user.role == "user":
            if not current_user.person_id:
                raise HTTPException(status_code=400, detail="User requires person_id")
            person_id_filter = current_user.person_id

        # Query base asset
        asset_query = db.query(Asset).filter(Asset.is_active == True)
        if person_id_filter:
            asset_query = asset_query.filter(Asset.person_id == person_id_filter)

        if status:
            asset_query = asset_query.filter(Asset.status == status)
        if asset_type_id:
            asset_query = asset_query.filter(Asset.asset_type_id == asset_type_id)

        total_assets = asset_query.count()
        assets_assigned = asset_query.filter(Asset.status == "assegnato").count()
        assets_available = asset_query.filter(Asset.status == "disponibile").count()

        # Low stock (solo admin/operatore)
        if current_user.role == "user":
            low_stock_items = 0
        else:
            low_stock_items = (
                db.query(InventorySku)
                .filter(
                    InventorySku.quantity <= InventorySku.min_quantity,
                    InventorySku.is_active == True,
                )
                .count()
            )

        # SIM attive (non filtrare per date)
        sim_query = db.query(Sim).filter(Sim.status == "assegnata")
        if person_id_filter:
            sim_query = sim_query.filter(Sim.person_id == person_id_filter)
        active_sims = sim_query.count()

        # Assignments con filtri date
        assignment_query = db.query(Assignment).filter(Assignment.status == "attivo")
        if person_id_filter:
            assignment_query = assignment_query.filter(Assignment.person_id == person_id_filter)

        if date_filter_start:
            assignment_query = assignment_query.filter(
                Assignment.assignment_date >= date_filter_start.date()
                if hasattr(date_filter_start, "date")
                else date_filter_start
            )
        if date_filter_end:
            assignment_query = assignment_query.filter(
                Assignment.assignment_date <= date_filter_end.date()
                if hasattr(date_filter_end, "date")
                else date_filter_end
            )
        if assignment_type:
            assignment_query = assignment_query.filter(
                Assignment.assignment_type == assignment_type
            )

        active_assignments = assignment_query.count()

        return {
            "total_assets": total_assets,
            "assets_assigned": assets_assigned,
            "assets_available": assets_available,
            "low_stock_items": low_stock_items,
            "active_sims": active_sims,
            "active_assignments": active_assignments,
        }
    except Exception as e:
        return {"error": str(e), "detail": "Errore nel recupero overview dashboard"}


@router.get("/assets-by-status")
def get_assets_by_status(
    status: Optional[str] = None,
    asset_type_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Conteggio assets per status (GROUP BY status) con filtri."""
    try:
        # Role-based filter
        person_id_filter = None
        if current_user.role == "user":
            if not current_user.person_id:
                raise HTTPException(status_code=400, detail="User requires person_id")
            person_id_filter = current_user.person_id

        query = db.query(
            Asset.status,
            func.count(Asset.id).label("count"),
        ).filter(Asset.is_active == True)
        if person_id_filter:
            query = query.filter(Asset.person_id == person_id_filter)

        if status:
            query = query.filter(Asset.status == status)
        if asset_type_id:
            query = query.filter(Asset.asset_type_id == asset_type_id)

        query = query.group_by(Asset.status)
        results = query.all()

        return [{"status": r.status, "count": r.count} for r in results]
    except Exception as e:
        logger.warning("Dashboard query failed: %s", e)
        return []


@router.get("/assets-by-type")
def get_assets_by_type(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Conteggio assets per tipo (solo tipi level=1, parent_id IS NULL) con filtri."""
    try:
        # Role-based filter
        person_id_filter = None
        if current_user.role == "user":
            if not current_user.person_id:
                raise HTTPException(status_code=400, detail="User requires person_id")
            person_id_filter = current_user.person_id

        query = (
            db.query(
                AssetType.name.label("type_name"),
                func.count(Asset.id).label("count"),
            )
            .select_from(Asset)
            .join(AssetType, Asset.asset_type_id == AssetType.id)
            .filter(Asset.is_active == True)
        )
        if person_id_filter:
            query = query.filter(Asset.person_id == person_id_filter)

        if status:
            query = query.filter(Asset.status == status)

        query = query.group_by(AssetType.name)
        results = query.all()

        return [{"type_name": r.type_name, "count": r.count} for r in results]
    except Exception as e:
        logger.warning("Dashboard query failed: %s", e)
        return []


@router.get("/assignments-timeline")
def get_assignments_timeline(
    days: Optional[int] = 365,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    assignment_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Conteggio assegnazioni per mese con filtri date e tipo."""
    try:
        if date_from:
            start_date = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            start_date = start_date.date() if hasattr(start_date, "date") else start_date
        else:
            start_date = datetime.utcnow().date() - timedelta(days=int(days) if days else 365)

        end_date = (
            datetime.fromisoformat(date_to.replace("Z", "+00:00")).date()
            if date_to
            else datetime.utcnow().date()
        )

        # Role-based filter
        person_id_filter = None
        if current_user.role == "user":
            if not current_user.person_id:
                raise HTTPException(status_code=400, detail="User requires person_id")
            person_id_filter = current_user.person_id

        assignments_list = (
            db.query(Assignment)
            .filter(
                Assignment.assignment_date >= start_date,
                Assignment.assignment_date <= end_date,
            )
        )
        if person_id_filter:
            assignments_list = assignments_list.filter(Assignment.person_id == person_id_filter)
        if assignment_type:
            assignments_list = assignments_list.filter(
                Assignment.assignment_type == assignment_type
            )
        assignments_list = assignments_list.all()

        from collections import defaultdict

        counts = defaultdict(int)
        for a in assignments_list:
            key = a.assignment_date.strftime("%Y-%m-%d")  # Formato giorno completo
            counts[key] += 1
        result = [{"date": k, "count": v} for k, v in sorted(counts.items())]
        return result
    except Exception as e:
        logger.warning("Dashboard query failed: %s", e)
        return []


@router.get("/recent-assignments")
def get_recent_assignments(
    days: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    assignment_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Ultime 10 assegnazioni con numero, persona, data, tipo e filtri."""
    try:
        # Role-based filter
        person_id_filter = None
        if current_user.role == "user":
            if not current_user.person_id:
                raise HTTPException(status_code=400, detail="User requires person_id")
            person_id_filter = current_user.person_id

        query = db.query(Assignment, Person).join(
            Person, Assignment.person_id == Person.id
        )
        if person_id_filter:
            query = query.filter(Assignment.person_id == person_id_filter)

        if days:
            start_date = datetime.utcnow().date() - timedelta(days=int(days))
            query = query.filter(Assignment.assignment_date >= start_date)
        elif date_from:
            start_date = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            if hasattr(start_date, "date"):
                start_date = start_date.date()
            query = query.filter(Assignment.assignment_date >= start_date)

        if date_to:
            end_date = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            if hasattr(end_date, "date"):
                end_date = end_date.date()
            query = query.filter(Assignment.assignment_date <= end_date)

        if assignment_type:
            query = query.filter(Assignment.assignment_type == assignment_type)

        rows = query.order_by(desc(Assignment.created_at)).limit(10).all()

        return [
            {
                "assignment_number": a.assignment_number,
                "person_name": f"{p.first_name} {p.last_name}".strip(),
                "assignment_date": a.assignment_date.isoformat() if a.assignment_date else None,
                "assignment_type": a.assignment_type,
            }
            for a, p in rows
        ]
    except Exception as e:
        logger.warning("Dashboard query failed: %s", e)
        return []


@router.get("/low-stock-items")
def get_low_stock_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Lista materiali sotto soglia minima con dettagli categoria, device, brand."""
    # Solo admin e operatori possono vedere il magazzino
    if current_user.role == "user":
        return []

    try:
        results = (
            db.query(InventorySku)
            .filter(
                InventorySku.quantity <= InventorySku.min_quantity,
                InventorySku.is_active == True,
            )
            .order_by(InventorySku.quantity.asc())
            .all()
        )
        return [
            {
                "id": sku.id,
                "category": sku.category or "N/A",
                "device": sku.device or "N/A",
                "brand": sku.brand or "N/A",
                "quantity": sku.quantity,
                "min_quantity": sku.min_quantity,
            }
            for sku in results
        ]
    except Exception as e:
        logger.warning("Error in low-stock-items: %s", e)
        return []

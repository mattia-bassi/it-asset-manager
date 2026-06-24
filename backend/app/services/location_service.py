from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.asset import Asset
from app.models.location import Location
from app.models.location_type import LocationType
from app.models.site import Site
from app.schemas.location import (
    LocationCreate,
    LocationListResponse,
    LocationResponse,
    LocationTypeCreate,
    LocationTypeListResponse,
    LocationTypeResponse,
    LocationTypeUpdate,
    LocationUpdate,
)


def _build_location_response(location: Location) -> LocationResponse:
    """Costruisce LocationResponse con campi denormalizzati."""
    location_type_name = location.location_type.name if location.location_type else None
    location_type_icon = location.location_type.icon if location.location_type else None
    site_name = location.site.name if location.site else None

    # display_name: "Nome — Sede, Piano, Stanza X" (parti opzionali omesse se NULL)
    display_name = None
    if location.name and site_name:
        display_name = f"{location.name} — {site_name}"
        extras = []
        if location.floor:
            extras.append(location.floor)
        if location.room_number:
            extras.append(f"Stanza {location.room_number}")
        if extras:
            display_name += ", " + ", ".join(extras)

    return LocationResponse(
        id=location.id,
        name=location.name,
        location_type_id=location.location_type_id,
        site_id=location.site_id,
        floor=location.floor,
        room_number=location.room_number,
        notes=location.notes,
        is_active=location.is_active,
        location_type_name=location_type_name,
        location_type_icon=location_type_icon,
        site_name=site_name,
        display_name=display_name,
        created_at=location.created_at,
        updated_at=location.updated_at,
    )


# --- LocationType CRUD ---


def get_location_types(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
) -> LocationTypeListResponse:
    """Recupera tutti i tipi di locazione con filtri opzionali."""
    query = select(LocationType)
    if is_active is not None:
        query = query.where(LocationType.is_active == is_active)

    count_query = select(LocationType)
    if is_active is not None:
        count_query = count_query.where(LocationType.is_active == is_active)
    total = db.scalar(select(func.count()).select_from(count_query.subquery())) or 0

    query = query.order_by(LocationType.name).offset(skip).limit(limit)
    types = db.scalars(query).all()

    items = [LocationTypeResponse.model_validate(t) for t in types]
    return LocationTypeListResponse(items=items, total=total)


def get_location_type(db: Session, location_type_id: int) -> Optional[LocationTypeResponse]:
    """Recupera un tipo di locazione per ID."""
    lt = db.scalar(select(LocationType).where(LocationType.id == location_type_id))
    if not lt:
        return None
    return LocationTypeResponse.model_validate(lt)


def create_location_type(db: Session, data: LocationTypeCreate) -> LocationTypeResponse:
    """Crea un nuovo tipo di locazione."""
    existing = db.scalar(select(LocationType).where(LocationType.name == data.name))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Esiste già un tipo di locazione con nome '{data.name}'",
        )
    location_type = LocationType(**data.model_dump())
    db.add(location_type)
    db.commit()
    db.refresh(location_type)
    return LocationTypeResponse.model_validate(location_type)


def update_location_type(
    db: Session,
    location_type_id: int,
    data: LocationTypeUpdate,
) -> Optional[LocationTypeResponse]:
    """Aggiorna un tipo di locazione esistente."""
    location_type = db.scalar(select(LocationType).where(LocationType.id == location_type_id))
    if not location_type:
        return None

    update_data = data.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] != location_type.name:
        existing = db.scalar(select(LocationType).where(LocationType.name == update_data["name"]))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Esiste già un tipo di locazione con nome '{update_data['name']}'",
            )

    for field, value in update_data.items():
        setattr(location_type, field, value)
    db.commit()
    db.refresh(location_type)
    return LocationTypeResponse.model_validate(location_type)


def delete_location_type(db: Session, location_type_id: int) -> bool:
    """Soft delete: imposta is_active = False."""
    location_type = db.scalar(select(LocationType).where(LocationType.id == location_type_id))
    if not location_type:
        return False

    active_locations = db.scalar(
        select(func.count())
        .select_from(Location)
        .where(Location.location_type_id == location_type_id, Location.is_active == True)
    ) or 0
    if active_locations > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile disattivare: esistono locazioni attive collegate a questo tipo",
        )

    location_type.is_active = False
    db.commit()
    return True


# --- Location CRUD ---


def get_locations(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    site_id: Optional[int] = None,
    location_type_id: Optional[int] = None,
    is_active: Optional[bool] = None,
) -> LocationListResponse:
    """Recupera tutte le locazioni con filtri opzionali."""
    query = (
        select(Location)
        .options(joinedload(Location.location_type), joinedload(Location.site))
    )
    if site_id is not None:
        query = query.where(Location.site_id == site_id)
    if location_type_id is not None:
        query = query.where(Location.location_type_id == location_type_id)
    if is_active is not None:
        query = query.where(Location.is_active == is_active)

    count_query = select(Location)
    if site_id is not None:
        count_query = count_query.where(Location.site_id == site_id)
    if location_type_id is not None:
        count_query = count_query.where(Location.location_type_id == location_type_id)
    if is_active is not None:
        count_query = count_query.where(Location.is_active == is_active)
    total = db.scalar(select(func.count()).select_from(count_query.subquery())) or 0

    query = query.order_by(Location.name).offset(skip).limit(limit)
    locations = db.scalars(query).unique().all()

    items = [_build_location_response(loc) for loc in locations]
    return LocationListResponse(items=items, total=total)


def get_location(db: Session, location_id: int) -> Optional[LocationResponse]:
    """Recupera una locazione per ID con campi denormalizzati."""
    location = db.scalar(
        select(Location)
        .options(joinedload(Location.location_type), joinedload(Location.site))
        .where(Location.id == location_id)
    )
    if not location:
        return None
    return _build_location_response(location)


def create_location(db: Session, data: LocationCreate) -> LocationResponse:
    """Crea una nuova locazione."""
    if data.location_type_id is not None:
        location_type = db.scalar(
            select(LocationType).where(LocationType.id == data.location_type_id)
        )
        if not location_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tipo di locazione con ID {data.location_type_id} non trovato",
            )

    site = db.scalar(select(Site).where(Site.id == data.site_id))
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sede con ID {data.site_id} non trovata",
        )

    if data.location_type_id is not None:
        existing = db.scalar(
            select(Location).where(
                Location.name == data.name,
                Location.location_type_id == data.location_type_id,
                Location.site_id == data.site_id,
                Location.is_active == True,
            )
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esiste già una locazione con lo stesso nome, tipo e sede",
            )

    location = Location(**data.model_dump())
    db.add(location)
    db.commit()
    db.refresh(location)
    # Ricarica con relationships per campi denormalizzati
    location = db.scalar(
        select(Location)
        .options(joinedload(Location.location_type), joinedload(Location.site))
        .where(Location.id == location.id)
    )
    return _build_location_response(location)


def update_location(
    db: Session,
    location_id: int,
    data: LocationUpdate,
) -> Optional[LocationResponse]:
    """Aggiorna una locazione esistente."""
    location = db.scalar(
        select(Location)
        .options(joinedload(Location.location_type), joinedload(Location.site))
        .where(Location.id == location_id)
    )
    if not location:
        return None

    update_data = data.model_dump(exclude_unset=True)

    if "location_type_id" in update_data:
        lt = db.scalar(
            select(LocationType).where(LocationType.id == update_data["location_type_id"])
        )
        if not lt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tipo di locazione con ID {update_data['location_type_id']} non trovato",
            )

    if "site_id" in update_data:
        site = db.scalar(select(Site).where(Site.id == update_data["site_id"]))
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sede con ID {update_data['site_id']} non trovata",
            )

    name = update_data.get("name", location.name)
    loc_type_id = update_data.get("location_type_id", location.location_type_id)
    sid = update_data.get("site_id", location.site_id)
    if (name, loc_type_id, sid) != (location.name, location.location_type_id, location.site_id):
        existing = db.scalar(
            select(Location).where(
                Location.name == name,
                Location.location_type_id == loc_type_id,
                Location.site_id == sid,
                Location.id != location_id,
            )
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esiste già una locazione con lo stesso nome, tipo e sede",
            )

    for field, value in update_data.items():
        setattr(location, field, value)
    db.commit()
    db.refresh(location)
    # Ricarica con relationships per campi denormalizzati
    location = db.scalar(
        select(Location)
        .options(joinedload(Location.location_type), joinedload(Location.site))
        .where(Location.id == location_id)
    )
    return _build_location_response(location)


def delete_location(db: Session, location_id: int) -> bool:
    """Soft delete: imposta is_active = False."""
    location = db.scalar(select(Location).where(Location.id == location_id))
    if not location:
        return False

    active_assets = db.scalar(
        select(func.count())
        .select_from(Asset)
        .where(Asset.location_id == location_id, Asset.is_active == True)
    ) or 0
    if active_assets > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile disattivare: esistono asset attivi collegati a questa locazione",
        )

    location.is_active = False
    db.commit()
    return True

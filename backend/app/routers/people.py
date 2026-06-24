from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from app.api.deps import get_db, get_current_user, get_current_active_admin
from app.schemas.person import Person, PersonCreate, PersonUpdate, PersonList, PersonMerge
from app.services.person_service import PersonService
from app.models.user import User
import math

router = APIRouter(prefix="/people", tags=["People"])


@router.get("", response_model=PersonList)
def get_people(
    skip: int = Query(0, ge=0, description="Numero di record da saltare"),
    limit: int = Query(100, ge=1, le=1000, description="Numero massimo di record"),
    is_active: Optional[bool] = Query(None, description="Filtra per stato attivo"),
    site_id: Optional[int] = Query(None, description="Filtra per sede"),
    search: Optional[str] = Query(None, description="Ricerca per nome, cognome o email"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recupera la lista delle persone con paginazione e filtri."""
    people, total = PersonService.get_all(
        db=db,
        skip=skip,
        limit=limit,
        is_active=is_active,
        site_id=site_id,
        search=search
    )
    
    return {
        "items": people,
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "page_size": limit,
        "pages": math.ceil(total / limit) if limit > 0 else 1
    }


@router.get("/{person_id}", response_model=Person)
def get_person(person_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Recupera una persona per ID."""
    person = PersonService.get_by_id(db, person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona con ID {person_id} non trovata"
        )
    return person


@router.post("", response_model=Person, status_code=status.HTTP_201_CREATED)
def create_person(person_data: PersonCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Crea una nuova persona."""
    try:
        person = PersonService.create(db, person_data)
        return person
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{person_id}", response_model=Person)
def update_person(
    person_id: int,
    person_data: PersonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aggiorna una persona esistente."""
    try:
        person = PersonService.update(db, person_id, person_data)
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Persona con ID {person_id} non trovata"
            )
        return person
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_person(person_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Disattiva una persona (soft delete)."""
    success = PersonService.delete(db, person_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona con ID {person_id} non trovata"
        )


@router.delete("/{person_id}/hard", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_person(person_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_admin)):
    """Elimina definitivamente una persona dal database."""
    success = PersonService.hard_delete(db, person_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona con ID {person_id} non trovata"
        )


@router.post("/merge", response_model=Person)
def merge_people(merge_data: PersonMerge, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Unisce due persone: sposta i dati dalla source alla target e disattiva la source.
    """
    try:
        person = PersonService.merge(db, merge_data)
        return person
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


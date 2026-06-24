from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.badge import BadgeStatus, BadgeType
from app.schemas.badge import (
    Badge,
    BadgeCreate,
    BadgeUpdate,
    BadgeList
)
from app.services.badge_service import BadgeService
import math

router = APIRouter(prefix="/badges", tags=["Badges"])


@router.post("", response_model=Badge, status_code=status.HTTP_201_CREATED)
def create_badge(
    badge_data: BadgeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crea un nuovo Badge aziendale

    - **numero_badge**: Numero identificativo univoco
    - **tipo**: Tipo badge (dipendente/visitatore/temporaneo)
    - **status**: Status (attivo/disattivo/smarrito)
    - **data_emissione**: Data emissione badge
    - **data_scadenza**: Data scadenza (opzionale)
    - **site_id**: Sede di riferimento (opzionale)
    - **person_id**: Persona assegnata (opzionale)
    - **notes**: Note aggiuntive (opzionale)

    **Permessi:** Solo admin e operatori
    """
    # Solo admin e operatori possono creare badge
    if current_user.role == "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permessi per creare badge"
        )

    return BadgeService.create_badge(db, badge_data)


@router.get("", response_model=BadgeList)
def get_badges(
    skip: int = Query(0, ge=0, description="Numero di record da saltare"),
    limit: int = Query(100, ge=1, le=1000, description="Numero massimo di record"),
    search: Optional[str] = Query(None, description="Ricerca in numero badge, note"),
    status: Optional[BadgeStatus] = Query(None, description="Filtra per status"),
    tipo: Optional[BadgeType] = Query(None, description="Filtra per tipo"),
    site_id: Optional[int] = Query(None, description="Filtra per sede"),
    scaduti: Optional[bool] = Query(None, description="True=solo scaduti, False=solo validi"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ottiene lista Badge con filtri e paginazione

    **Filtri disponibili:**
    - **search**: Ricerca testuale in numero badge, note
    - **status**: Filtra per status (attivo/disattivo/smarrito)
    - **tipo**: Filtra per tipo (dipendente/visitatore/temporaneo)
    - **site_id**: Filtra per sede
    - **scaduti**: True per badge scaduti, False per validi, None per tutti

    **Permessi:** User vede solo i propri badge
    """
    # Role-based filter per user
    person_id_filter = None
    if current_user.role == "user":
        if not current_user.person_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Utente non collegato a nessuna persona"
            )
        person_id_filter = current_user.person_id

    badges, total = BadgeService.get_badges(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        tipo=tipo,
        site_id=site_id,
        scaduti=scaduti
    )

    # Filtra per person_id se user
    if person_id_filter:
        badges = [b for b in badges if b.person_id == person_id_filter]
        total = len(badges)

    # Calcola paginazione
    pages = math.ceil(total / limit) if total > 0 else 0
    page = (skip // limit) + 1

    return BadgeList(
        items=badges,
        total=total,
        page=page,
        page_size=limit,
        pages=pages
    )


@router.get("/scaduti/list", response_model=BadgeList)
def get_scaduti(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ottiene lista badge scaduti e ancora attivi

    Utile per report e notifiche

    **Permessi:** Solo admin e operatori
    """
    # Solo admin e operatori
    if current_user.role == "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permessi per visualizzare questa lista"
        )

    badges = BadgeService.get_scaduti(db)

    return BadgeList(
        items=badges,
        total=len(badges),
        page=1,
        page_size=len(badges),
        pages=1
    )


@router.get("/{badge_id}", response_model=Badge)
def get_badge(
    badge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ottiene dettagli di un Badge specifico

    **Permessi:** User può vedere solo il proprio badge
    """
    badge = BadgeService.get_badge_by_id(db, badge_id)

    if not badge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Badge con ID {badge_id} non trovato"
        )

    # User può vedere solo il proprio badge
    if current_user.role == "user":
        if not current_user.person_id or badge.person_id != current_user.person_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Non hai permessi per visualizzare questo badge"
            )

    return badge


@router.put("/{badge_id}", response_model=Badge)
def update_badge(
    badge_id: int,
    badge_data: BadgeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Aggiorna un Badge esistente

    **Permessi:** Solo admin e operatori
    """
    # Solo admin e operatori possono modificare badge
    if current_user.role == "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permessi per modificare badge"
        )

    return BadgeService.update_badge(db, badge_id, badge_data)


@router.delete("/{badge_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_badge(
    badge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Elimina un Badge (soft delete)

    Il badge viene disattivato (is_active=False, status=disattivo)

    **Permessi:** Solo admin e operatori
    """
    # Solo admin e operatori possono eliminare badge
    if current_user.role == "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permessi per eliminare badge"
        )

    BadgeService.delete_badge(db, badge_id)
    return None

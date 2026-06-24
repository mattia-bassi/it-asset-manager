from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.sim import SimStatus
from app.schemas.sim import (
    SimCreate,
    SimUpdate,
    SimResponse,
    SimWithCredentials,
    SimListResponse
)
from app.services.sim_service import SimService
import math

router = APIRouter(prefix="/sims", tags=["SIM Cards"])


@router.post("", response_model=SimResponse, status_code=status.HTTP_201_CREATED)
def create_sim(
    sim_data: SimCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crea una nuova SIM con PIN/PUK criptati
    
    - **seriale**: Seriale univoco della SIM
    - **operatore**: Operatore telefonico (TIM, Vodafone, Wind, etc.)
    - **numero_telefono**: Numero di telefono
    - **pin**: PIN SIM (4-8 cifre) - verrà criptato
    - **puk**: PUK SIM (8 cifre) - verrà criptato
    - **status**: Status iniziale (default: disponibile)
    """
    # Solo admin e operatori possono creare SIM
    if current_user.role == "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permessi per creare SIM"
        )
    return SimService.create_sim(db, sim_data)


@router.get("", response_model=SimListResponse)
def get_sims(
    skip: int = Query(0, ge=0, description="Numero di record da saltare"),
    limit: int = Query(100, ge=1, le=500, description="Numero massimo di record"),
    search: Optional[str] = Query(None, description="Ricerca in seriale, numero, operatore"),
    status: Optional[SimStatus] = Query(None, description="Filtra per status"),
    operatore: Optional[str] = Query(None, description="Filtra per operatore"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ottiene lista SIM con filtri e paginazione
    
    Filtri disponibili:
    - **search**: Ricerca testuale in seriale, numero telefono, operatore
    - **status**: Filtra per status (disponibile, assegnata, disattivata)
    - **operatore**: Filtra per operatore telefonico
    """
    # Role-based filter
    person_id_filter = None
    if current_user.role == "user":
        if not current_user.person_id:
            raise HTTPException(status_code=400, detail="User requires person_id")
        person_id_filter = current_user.person_id

    sims, total = SimService.get_sims(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        operatore=operatore
    )

    # Filtra per person_id se user
    if person_id_filter:
        sims = [s for s in sims if s.get("person_id") == person_id_filter]
        total = len(sims)

    # Calcola numero pagine
    pages = math.ceil(total / limit) if total > 0 else 0
    page = (skip // limit) + 1
    
    return SimListResponse(
        items=sims,
        total=total,
        page=page,
        page_size=limit,
        pages=pages
    )


@router.get("/{sim_id}", response_model=SimResponse)
def get_sim(
    sim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ottiene dettagli di una SIM specifica
    
    **Nota**: PIN e PUK non sono inclusi in questa risposta per sicurezza.
    Usa l'endpoint /sims/{sim_id}/credentials per ottenerli.
    """
    sim = SimService.get_sim_by_id(db, sim_id)
    if not sim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SIM con ID {sim_id} non trovata"
        )
    # Role-based access control
    if current_user.role == "user":
        if not current_user.person_id:
            raise HTTPException(status_code=400, detail="User requires person_id")
        if sim.person_id != current_user.person_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Non hai accesso a questa SIM"
            )
    return sim


@router.put("/{sim_id}", response_model=SimResponse)
def update_sim(
    sim_id: int,
    sim_data: SimUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Aggiorna una SIM esistente
    
    Tutti i campi sono opzionali. Solo i campi forniti verranno aggiornati.
    Se forniti, PIN e PUK verranno automaticamente criptati.
    """
    # Solo admin e operatori possono modificare SIM
    if current_user.role == "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permessi per modificare SIM"
        )
    return SimService.update_sim(db, sim_id, sim_data)


@router.delete("/{sim_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sim(
    sim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Elimina una SIM
    
    **Nota**: Non è possibile eliminare SIM con status "assegnata".
    Rimuovere prima l'assegnazione.
    """
    # Solo admin può eliminare SIM
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo gli amministratori possono eliminare SIM"
        )
    SimService.delete_sim(db, sim_id)
    return None


@router.get("/{sim_id}/credentials", response_model=SimWithCredentials)
def get_sim_credentials(
    sim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ottiene credenziali decriptate (PIN e PUK) di una SIM
    
    ⚠️ **Endpoint sensibile**: Restituisce PIN e PUK in chiaro.
    Riservato agli amministratori. Utilizzare solo quando necessario.
    
    **Caso d'uso**: Generazione PDF di assegnazione con credenziali.
    """
    # SECURITY: Solo admin/operatore possono vedere credenziali; user solo delle proprie SIM
    if current_user.role == "user":
        if not current_user.person_id:
            raise HTTPException(status_code=400, detail="User requires person_id")
        sim_check = SimService.get_sim_by_id(db, sim_id)
        if not sim_check:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SIM con ID {sim_id} non trovata"
            )
        if sim_check.person_id != current_user.person_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Non puoi visualizzare credenziali di SIM non tue"
            )

    sim = SimService.get_sim_by_id(db, sim_id)
    if not sim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SIM con ID {sim_id} non trovata"
        )
    
    # Ottieni credenziali decriptate
    credentials = SimService.get_sim_credentials(db, sim_id)
    
    # Costruisci risposta con credenziali
    return SimWithCredentials(
        id=sim.id,
        seriale=sim.seriale,
        operatore=sim.operatore,
        numero_telefono=sim.numero_telefono,
        status=sim.status,
        created_at=sim.created_at,
        updated_at=sim.updated_at,
        pin=credentials["pin"],
        puk=credentials["puk"]
    )


@router.post("/{sim_id}/assign/{person_id}", response_model=SimResponse)
def assign_sim_to_person(
    sim_id: int,
    person_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Assegna una SIM a una persona
    
    Azioni automatiche:
    - Status SIM → "assegnata"
    - Campo "mobile_phone" della persona → numero telefono SIM
    
    **Prerequisiti**:
    - SIM deve avere status "disponibile"
    - Persona deve esistere
    """
    # Solo admin e operatori possono assegnare SIM
    if current_user.role == "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permessi per assegnare SIM"
        )
    return SimService.assign_sim_to_person(db, sim_id, person_id)


@router.post("/{sim_id}/unassign/{person_id}", response_model=SimResponse)
def unassign_sim_from_person(
    sim_id: int,
    person_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Rimuove assegnazione SIM da una persona
    
    Azioni automatiche:
    - Status SIM → "disponibile"
    - Campo "mobile_phone" della persona → NULL (se corrisponde al numero SIM)
    """
    # Solo admin e operatori possono disassegnare SIM
    if current_user.role == "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permessi per disassegnare SIM"
        )
    return SimService.unassign_sim(db, sim_id, person_id)


@router.get("/by-seriale/{seriale}", response_model=SimResponse)
def get_sim_by_seriale(
    seriale: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ottiene una SIM tramite il suo seriale univoco
    
    Utile per ricerche rapide o QR code scanning.
    """
    sim = SimService.get_sim_by_seriale(db, seriale)
    if not sim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SIM con seriale '{seriale}' non trovata"
        )
    # Role-based access control
    if current_user.role == "user":
        if not current_user.person_id:
            raise HTTPException(status_code=400, detail="User requires person_id")
        if sim.person_id != current_user.person_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Non hai accesso a questa SIM"
            )
    return sim

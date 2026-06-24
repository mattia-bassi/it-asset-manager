from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.models.user import User
from app.models.person import Person
from app.schemas.user import UserCreate, UserUpdate, UserOut, UserChangeRole, UserLinkPerson
from app.api.deps import get_db, get_current_active_admin, get_current_user
from app.core.security import hash_password
from app.services.audit_service import AuditService

router = APIRouter(prefix="/users", tags=["users"])


def _enrich_user_out(user) -> dict:
    """Populate person fields in UserOut response."""
    data = {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active,
        "person_id": user.person_id,
        "created_at": user.created_at,
        "person_first_name": None,
        "person_last_name": None,
        "person_email": None,
    }
    if user.person_id and hasattr(user, 'person') and user.person:
        data["person_first_name"] = user.person.first_name
        data["person_last_name"] = user.person.last_name
        data["person_email"] = user.person.email
    return data


@router.get("/")
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: bool | None = None,
    role: str | None = None,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Lista utenti (solo admin)"""
    query = db.query(User).filter(User.username != "master")
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if role:
        query = query.filter(User.role == role)

    total = query.count()
    users = query.options(joinedload(User.person)).offset(skip).limit(limit).all()
    return {"items": [_enrich_user_out(u) for u in users], "total": total}


@router.get("/{user_id}")
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Dettaglio utente (solo admin)"""
    user = db.query(User).options(joinedload(User.person)).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    if user.username == "master":
        raise HTTPException(status_code=404, detail="Utente non trovato")
    return _enrich_user_out(user)


@router.post("/", response_model=UserOut, status_code=201)
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Crea nuovo utente (solo admin)"""
    # Verifica username univoco
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username già esistente")
    
    # Crea utente
    new_user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        is_active=user_data.is_active
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Aggiorna utente (solo admin)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    if user.username == "master":
        raise HTTPException(status_code=403, detail="Operazione non consentita")
    
    # Verifica username univoco se viene modificato
    if user_data.username and user_data.username != user.username:
        existing = db.query(User).filter(User.username == user_data.username).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username già esistente")
        user.username = user_data.username
    
    # Aggiorna campi
    if user_data.role is not None:
        user.role = user_data.role
    
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    if user_data.password:
        user.password_hash = hash_password(user_data.password)
    
    db.commit()
    db.refresh(user)
    
    return user

@router.patch("/{user_id}/role", response_model=UserOut)
def change_user_role(
    user_id: int,
    role_data: UserChangeRole,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Cambia ruolo utente (solo admin)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    if user.username == "master":
        raise HTTPException(status_code=403, detail="Operazione non consentita")
    
    # Non permettere di modificare il proprio ruolo
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Non puoi modificare il tuo stesso ruolo")
    
    user.role = role_data.role
    db.commit()
    db.refresh(user)
    
    return user

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Elimina utente (solo admin) - soft delete"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    if user.username == "master":
        raise HTTPException(status_code=403, detail="Operazione non consentita")
    
    # Non permettere di eliminare se stesso
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Non puoi eliminare il tuo stesso account")
    
    # Soft delete
    user.is_active = False
    db.commit()
    
    return {"message": f"Utente {user.username} disattivato con successo"}


@router.delete("/{user_id}/hard")
def hard_delete_user(
    user_id: int,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Eliminazione permanente utente dal database (solo admin)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    if user.username == "master":
        raise HTTPException(status_code=403, detail="Operazione non consentita")

    # Non permettere di eliminare se stesso
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Non puoi eliminare il tuo stesso account")

    # Non permettere di eliminare l'admin principale (id=1)
    if user.id == 1:
        raise HTTPException(status_code=400, detail="Non puoi eliminare l'account admin principale")

    username = user.username
    user_id_deleted = user.id

    # Audit log PRIMA della cancellazione
    AuditService.log_action(
        db=db,
        action="DELETE",
        entity_type="user",
        entity_id=user_id_deleted,
        user_id=current_user.id,
        username=current_user.username,
        details=f"User {username} (id={user_id_deleted}) permanently deleted",
        old_value={"username": username, "role": user.role, "person_id": user.person_id}
    )

    db.delete(user)
    db.commit()

    return {"message": f"Utente {username} eliminato permanentemente"}


@router.patch("/{user_id}/link-person")
def link_user_to_person(
    user_id: int,
    payload: UserLinkPerson,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """Link an orphan user to an existing person. Admin only."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    if user.username == "master":
        raise HTTPException(status_code=403, detail="Operazione non consentita")

    # Verify person exists
    person = db.query(Person).filter(Person.id == payload.person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Persona non trovata")

    # Check person not already linked to another user
    existing = db.query(User).filter(
        User.person_id == payload.person_id,
        User.id != user_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Persona già collegata all'utente '{existing.username}'"
        )

    old_person_id = user.person_id
    user.person_id = payload.person_id
    db.commit()
    db.refresh(user)

    # Audit log
    AuditService.log_action(
        db=db,
        action="UPDATE",
        entity_type="user",
        entity_id=user_id,
        user_id=current_user.id,
        username=current_user.username,
        details=f"User {user.username} linked to person_id={payload.person_id}",
        old_value={"person_id": old_person_id},
        new_value={"person_id": payload.person_id}
    )

    # Reload with person relationship
    user = db.query(User).options(joinedload(User.person)).filter(User.id == user_id).first()
    return _enrich_user_out(user)

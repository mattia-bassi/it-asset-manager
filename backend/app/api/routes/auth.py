from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, rate_limit_login, rate_limit_change_password
from app.core.security import hash_password, verify_password
from app.models.person import Person
from app.models.user import User
from app.schemas.auth import TokenOut, MeOut, ChangePasswordIn
from app.services.audit_service import AuditService
from app.services.auth_service import login_user

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class MasterSetupRequest(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    site_id: Optional[int] = None
    username: str
    password: str


@router.post("/auth/master-setup")
def master_setup(payload: MasterSetupRequest, db: Session = Depends(get_db)):
    """Setup iniziale account master: crea admin e disabilita master."""
    master = db.query(User).filter(User.username == "master").first()
    if not master:
        raise HTTPException(status_code=404, detail="Account master non trovato")

    if master.is_permanently_disabled:
        raise HTTPException(
            status_code=403,
            detail="Setup già completato. Account master disabilitato."
        )

    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username già in uso")

    if len(payload.password) < 12:
        raise HTTPException(status_code=400, detail="La password deve essere di almeno 12 caratteri")

    person = Person(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email if payload.email else None,
        site_id=payload.site_id if payload.site_id else None,
        is_active=True
    )
    db.add(person)
    db.flush()

    new_admin = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role="admin",
        is_active=True,
        is_permanently_disabled=False,
        person_id=person.id
    )
    db.add(new_admin)

    master.is_permanently_disabled = True
    master.is_active = False

    db.commit()

    return {"message": "Setup completato. Accedi con le credenziali impostate."}


@router.post("/auth/login")
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit_login),
):
    try:
        result = login_user(username=form.username, password=form.password, db=db)
    except HTTPException:
        # Audit log per tentativo di login fallito
        try:
            AuditService.log_action(
                db=db,
                action="LOGIN_FAILED",
                entity_type="user",
                details=f"Tentativo di login fallito per username: {form.username}",
                username=form.username,
                request=request
            )
        except Exception as e:
            logger.warning("Audit log failed: %s", e)
        raise

    if result.get("require_master_setup"):
        return result

    user = db.query(User).filter(User.username == form.username).first()
    # Audit log per login riuscito
    try:
        AuditService.log_action(
            db=db,
            action="LOGIN",
            entity_type="user",
            entity_id=user.id,
            user_id=user.id,
            username=user.username,
            details=f"Login riuscito: {user.username} ({user.role})",
            request=request
        )
    except Exception as e:
        logger.warning("Audit log failed: %s", e)

    return TokenOut(**result)

@router.get("/auth/me", response_model=MeOut)
def me(current: User = Depends(get_current_user)):
    return MeOut(username=current.username, role=current.role)

@router.post("/auth/change-password")
def change_password(
    request: Request,
    password_data: ChangePasswordIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit_change_password),
):
    """Cambia la password dell'utente autenticato"""
    # Verifica password vecchia
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Password corrente non valida")
    
    # Verifica lunghezza nuova password
    if len(password_data.new_password) < 8:
        raise HTTPException(status_code=400, detail="La nuova password deve essere di almeno 8 caratteri")
    
    # Aggiorna password
    current_user.password_hash = hash_password(password_data.new_password)
    db.commit()

    # Audit log per cambio password
    try:
        AuditService.log_action(
            db=db,
            action="CHANGE_PASSWORD",
            entity_type="user",
            entity_id=current_user.id,
            user_id=current_user.id,
            username=current_user.username,
            details=f"Password cambiata per utente: {current_user.username}",
            request=request
        )
    except Exception as e:
        logger.warning("Audit log failed: %s", e)

    return {"message": "Password cambiata con successo"}

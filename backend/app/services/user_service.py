from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.user import User

MASTER_USERNAME = "master"


def get_all(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    role: Optional[str] = None,
) -> tuple[list, int]:
    """
    Recupera la lista degli utenti con filtri.
    Esclude l'account master dalla lista.
    Ritorna (lista_utenti, totale).
    """
    query = db.query(User).filter(User.username != MASTER_USERNAME)

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if role:
        query = query.filter(User.role == role)

    total = query.count()
    users = query.options(joinedload(User.person)).offset(skip).limit(limit).all()
    return users, total


def get_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Recupera un utente per ID.
    Restituisce None se l'utente è master (per impedire accesso diretto).
    """
    user = db.query(User).options(joinedload(User.person)).filter(User.id == user_id).first()
    if not user or user.username == MASTER_USERNAME:
        return None
    return user

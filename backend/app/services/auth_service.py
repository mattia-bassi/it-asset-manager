from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.auth import TokenOut


def login_user(
    username: str,
    password: str,
    db: Session,
) -> dict[str, Any]:
    """
    Autentica l'utente e restituisce token o segnale setup master.
    - Password errata → HTTPException 401
    - master + is_permanently_disabled → HTTPException 403
    - master + password corretta → {"require_master_setup": True}
    - altri utenti → TokenOut come dict
    """
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Master account special handling
    if user.username == "master":
        if user.is_permanently_disabled:
            raise HTTPException(
                status_code=403,
                detail="Account disabilitato permanentemente"
            )
        return {"require_master_setup": True}

    token = create_access_token(user.username)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "person_id": user.person_id,
        }
    }

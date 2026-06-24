from typing import List
from functools import wraps
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.rate_limit import check_rate_limit
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

bearer = HTTPBearer(auto_error=False)

def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(creds.credentials)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found/inactive")
    return user

def require_role(allowed_roles: List[str]):
    """
    Decorator per verificare che l'utente abbia uno dei ruoli richiesti.
    Usage: @require_role(['admin'])
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Trova il parametro current_user nei kwargs
            current_user = kwargs.get('current_user')
            if not current_user:
                # Cerca tra gli args
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break
            
            if not current_user:
                raise HTTPException(status_code=401, detail="User not authenticated")
            
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Accesso negato. Ruolo richiesto: {', '.join(allowed_roles)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def get_current_active_admin(current_user: User = Depends(get_current_user)) -> User:
    """Verifica che l'utente sia admin"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Solo gli admin possono accedere a questa risorsa")
    return current_user


async def rate_limit_login(request: Request) -> None:
    """
    Dependency per rate limiting login endpoint.
    Max 5 tentativi al minuto per IP.

    Raises:
        HTTPException 429: Se rate limit superato
    """
    await check_rate_limit(request, "login")


async def rate_limit_gdpr(request: Request) -> None:
    """
    Dependency per rate limiting endpoint GDPR.

    Raises:
        HTTPException 429: Se rate limit superato
    """
    await check_rate_limit(request, "gdpr_access")


async def rate_limit_change_password(request: Request) -> None:
    """Rate limit per cambio password (per IP)."""
    await check_rate_limit(request, "change_password")

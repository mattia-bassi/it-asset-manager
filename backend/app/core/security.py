from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["argon2", "pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password using Argon2. Validates input before hashing."""
    if not password:
        raise ValueError("Password cannot be empty")
    password = password.strip()
    if len(password) < settings.password_min_length:
        raise ValueError(f"Password must be at least {settings.password_min_length} characters long")
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash. Returns False for unrecognized hashes (no crash)."""
    if not password:
        return False
    password = password.strip()
    try:
        return pwd_context.verify(password, password_hash)
    except (ValueError, TypeError):
        # Handle unrecognized hash formats gracefully
        return False

def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algo)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algo])

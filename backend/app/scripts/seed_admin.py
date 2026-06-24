import sys
import logging
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Validate admin username
    if not settings.admin_username or not settings.admin_username.strip():
        logger.error("ADMIN_USERNAME is empty or missing. Cannot create admin user.")
        logger.error("Please set ADMIN_USERNAME in your .env file.")
        sys.exit(1)
    
    # Validate admin password before proceeding
    if not settings.admin_password or not settings.admin_password.strip():
        logger.error("ADMIN_PASSWORD is empty or missing. Cannot create admin user.")
        logger.error("Please set ADMIN_PASSWORD in your .env file with a password of at least 8 characters.")
        sys.exit(1)
    
    try:
        # Validate password format (will raise ValueError if invalid)
        hash_password(settings.admin_password)
    except ValueError as e:
        logger.error(f"ADMIN_PASSWORD validation failed: {e}")
        logger.error("Please set a valid ADMIN_PASSWORD (at least 8 characters) in your .env file.")
        sys.exit(1)
    
    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == settings.admin_username).first()
        if existing:
            logger.info(f"[seed] admin already exists: {settings.admin_username}")
            return
        
        user = User(
            username=settings.admin_username,
            password_hash=hash_password(settings.admin_password),
            role="admin",
            is_active=True,
        )
        db.add(user)
        db.commit()
        logger.info(f"[seed] admin created: {settings.admin_username}")
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()


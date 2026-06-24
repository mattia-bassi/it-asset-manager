"""
Script di verifica integrità database.
Controlla che tutte le tabelle essenziali esistano.
"""
import logging
from sqlalchemy import inspect
from app.db.session import engine

logger = logging.getLogger(__name__)

# Tabelle essenziali che DEVONO esistere
ESSENTIAL_TABLES = [
    'users',
    'people',
    'sites',
    'asset_types',
    'assets',
    'inventory_skus',
    'assignments',
    'assignment_items',
    'sims',
    'badges',
    'audit_logs',
    'document_templates',  # Aggiunta dopo fix 11 Feb 2026
    'alembic_version'
]


def verify_tables():
    """Verifica che tutte le tabelle essenziali esistano."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    missing_tables = set(ESSENTIAL_TABLES) - existing_tables

    if missing_tables:
        logger.error(f"❌ TABELLE MANCANTI: {', '.join(missing_tables)}")
        logger.error("Esegui 'alembic upgrade head' o contatta l'amministratore")
        return False

    logger.info(f"✅ Tutte le {len(ESSENTIAL_TABLES)} tabelle essenziali sono presenti")
    return True


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    if not verify_tables():
        sys.exit(1)

#!/usr/bin/env python3
"""
Script per rotazione automatica audit logs. Eseguibile via cron o manualmente.
Uso: python scripts/log_rotation.py [--retention-months 24]
"""

import sys
import os
import argparse
import logging
import datetime

# Aggiungi il path dell'app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Setup logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--retention-months",
        type=int,
        default=24,
        help="Mesi di retention log"
    )
    args = parser.parse_args()

    logger.info("Starting audit log rotation (retention: %d months)", args.retention_months)

    from app.db.session import SessionLocal
    from app.services.audit_service import AuditService

    db = SessionLocal()
    try:
        result = AuditService.rotate_logs(db=db, retention_months=args.retention_months)

        if "error" in result:
            logger.error("Log rotation failed: %s", result["error"])
            sys.exit(1)

        logger.info(
            "Log rotation completed: archived_count=%d, archive_file=%s, remaining_count=%d",
            result.get("archived_count", 0),
            result.get("archive_file") or "N/A",
            result.get("remaining_count", 0)
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()

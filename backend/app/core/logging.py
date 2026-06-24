import logging
import os
from logging.handlers import RotatingFileHandler
from app.core.config import settings

def setup_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)

    fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

    # stdout
    sh = logging.StreamHandler()
    sh.setLevel(level)
    sh.setFormatter(fmt)
    root.handlers = [sh]

    # optional file
    log_path = "/data/log/app.log"
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        fh = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=3)
        fh.setLevel(level)
        fh.setFormatter(fmt)
        root.addHandler(fh)
    except Exception as e:
        # Log volume not mounted — falling back to stdout only
        logging.getLogger(__name__).debug("Log file handler not available: %s", e)


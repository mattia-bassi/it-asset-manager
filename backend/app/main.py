from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import logging
import os

from app.core.config import settings
from app.core.cors import CORS_ORIGINS, get_cors_headers
from app.core.logging import setup_logging
from app.core.rate_limit import setup_rate_limiting
from app.core.security import hash_password
from app.api.router import api_router
from app.db.session import SessionLocal
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.models.user import User

setup_logging()
logger = logging.getLogger(__name__)

DIST_DIR = Path("/app/static/dist")

app = FastAPI(title=settings.app_name)


class AddCORSHeadersMiddleware:
    """Middleware ASGI puro: aggiunge CORS a OGNI risposta leggendo response_start."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        origin = None
        for h in scope.get("headers") or []:
            if h[0] == b"origin":
                origin = h[1].decode("latin-1").strip()
                break

        async def send_with_cors(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                has_origin = any(h[0].lower() == b"access-control-allow-origin" for h in headers)
                if origin and origin in CORS_ORIGINS and not has_origin:
                    headers.append((b"access-control-allow-origin", origin.encode()))
                    headers.append((b"access-control-allow-credentials", b"true"))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_cors)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Errori 500 con header CORS così il frontend può leggere la risposta."""
    if isinstance(exc, HTTPException):
        raise exc
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers=get_cors_headers(request),
    )


@app.exception_handler(StarletteHTTPException)
async def spa_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        path = request.url.path
        # Chiamata API che non esiste → JSON 404
        if path.startswith("/api/"):
            return JSONResponse(
                status_code=404,
                content={"detail": "API endpoint not found"},
                headers=get_cors_headers(request),
            )
        # File statici che non esistono → 404 normale
        if path.startswith("/data/"):
            return JSONResponse(
                status_code=404,
                content={"detail": "File not found"},
            )
        # /assets/*.js|css|etc → file statico mancante → 404
        # /assets (senza estensione) → route SPA → serve index.html
        if path.startswith("/assets/") and "." in path.split("/")[-1]:
            return JSONResponse(
                status_code=404,
                content={"detail": "File not found"},
            )
        # Tutto il resto → React Router (serve index.html)
        index_path = DIST_DIR / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
    # Per altri errori HTTP (401, 403, 500...) → comportamento standard
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=get_cors_headers(request),
    )


# Setup rate limiting
setup_rate_limiting(app)

# Security headers (OWASP best practices - ISO 27001 A.14.1.2)
app.add_middleware(SecurityHeadersMiddleware)

# CORS standard (preflight, Allow-Origin su risposte normali)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ASGI puro: inietta CORS in ogni http.response.start (incluse 500 e file)
app.add_middleware(AddCORSHeadersMiddleware)

app.include_router(api_router)


# Seed master account (if not exists)
@app.on_event("startup")
def seed_master():
    master_pw = os.getenv("MASTER_PASSWORD", "")
    if not master_pw:
        logger.warning("MASTER_PASSWORD not set, skipping master seed")
        return
    db = SessionLocal()
    try:
        master = db.query(User).filter(User.username == "master").first()
        if not master:
            master_user = User(
                username="master",
                password_hash=hash_password(master_pw),
                role="admin",
                is_active=True,
                is_permanently_disabled=False
            )
            db.add(master_user)
            db.commit()
            logger.info("[seed] master account created")
        else:
            logger.info("[seed] master account already exists: %s (disabled=%s)",
                        master.username, master.is_permanently_disabled)
    except Exception as e:
        logger.exception("Failed to seed master account: %s", e)
        db.rollback()
    finally:
        db.close()


# Serve frontend static files (CSS, JS) OR SPA fallback
@app.get("/assets/{filepath:path}")
async def serve_frontend_assets(filepath: str):
    dist_root = DIST_DIR.resolve()
    full_path = (DIST_DIR / "assets" / filepath).resolve()
    if not full_path.is_relative_to(dist_root):
        raise HTTPException(status_code=403, detail="Forbidden")
    file_path = full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    index_path = DIST_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    raise HTTPException(status_code=404, detail="Not found")

# Serve index.html per root
@app.get("/")
async def serve_root():
    index_path = DIST_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Frontend not found"}


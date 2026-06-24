"""
Rate Limiting - Protezione API da abusi e brute force attacks.

Compliance:
- ISO 27001:2022 - A.14.2.8 (Capacity management)
- OWASP Top 10 - A04:2021 (Insecure Design)

Libreria: slowapi (FastAPI/Starlette integration)
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)

# Configurabile da environment
DEFAULT_LIMIT = os.getenv("RATE_LIMIT_API", "200/minute")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
LOGIN_LIMIT = os.getenv("RATE_LIMIT_LOGIN", "5/minute")

# Dizionario limiti specifici per tipo endpoint
# Formato: "count/period" (es. "5/minute", "10/hour")
RATE_LIMITS: dict[str, str] = {
    "login": "5/minute",  # Brute force protection - OWASP
    "change_password": "3/minute",
    "create": "30/minute",
    "update": "50/minute",
    "delete": "20/minute",
    "read": "100/minute",
    "list": "50/minute",
    "export": "5/minute",  # Operazioni pesanti
    "report": "10/minute",
    "gdpr_access": "10/hour",
    "gdpr_portability": "5/hour",
    "gdpr_erasure": "2/hour",  # Azione critica
    "gdpr_rectification": "10/minute",
    "gdpr_restriction": "5/hour",
}

# Storage condiviso per check_rate_limit manuale (diverso da limiter slowapi)
# Usa memoria; per produzione considerare Redis condiviso
_manual_check_storage: Optional[object] = None


def _get_manual_storage():
    """Lazy init storage per check_rate_limit."""
    global _manual_check_storage
    if _manual_check_storage is None:
        try:
            from limits.storage import storage_from_string
            _manual_check_storage = storage_from_string(REDIS_URL)
        except ImportError:
            _manual_check_storage = False  # limits non disponibile
    return _manual_check_storage if _manual_check_storage else None


# Limiter slowapi - configurazione principale
# ISO 27001 A.14.2.8: Capacity management per prevenire DoS
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[DEFAULT_LIMIT],
    storage_uri=REDIS_URL,  # Redis per persistenza contatori tra restart
    strategy="fixed-window",  # Fixed window vs sliding window
    headers_enabled=True,  # X-RateLimit-* headers nelle risposte
    swallow_errors=False,  # Abilita rate limiting (errori vengono propagati)
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler per RateLimitExceeded.
    
    Restituisce 429 Too Many Requests con:
    - JSON body (error, message, detail)
    - Retry-After header
    - Logging per audit
    
    Args:
        request: FastAPI Request
        exc: RateLimitExceeded exception
        
    Returns:
        JSONResponse con status 429
    """
    try:
        # Estrai IP e path per logging
        client_ip = get_remote_address(request)
        path = request.url.path
        
        logger.warning(
            "Rate limit exceeded: IP=%s path=%s method=%s",
            client_ip,
            path,
            request.method,
        )
        
        # Retry-After (secondi) - slowapi potrebbe fornirlo in exc.description
        retry_after = 60  # Default 1 minuto
        if hasattr(exc, "description") and exc.description:
            # Estrai secondi da description se disponibile
            try:
                retry_after = int(exc.description)
            except (ValueError, TypeError) as e:
                logger.debug("Could not parse Retry-After from exc.description: %s", e)
        
        response = JSONResponse(
            status_code=429,
            content={
                "error": "rate_limit_exceeded",
                "message": "Troppe richieste. Riprova più tardi.",
                "detail": "Hai superato il limite di richieste consentito. Attendi prima di riprovare.",
            },
        )
        response.headers["Retry-After"] = str(retry_after)
        
        return response
        
    except Exception as e:
        logger.error("Error in rate_limit_exceeded_handler: %s", e)
        # Fallback: risposta minima
        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limit_exceeded",
                "message": "Troppe richieste.",
                "detail": str(exc) if str(exc) else "Rate limit exceeded",
            },
        )


def setup_rate_limiting(app) -> None:
    """
    Setup rate limiting sull'app FastAPI.
    Registra il limiter in app.state, il middleware e l'exception handler.
    
    Args:
        app: FastAPI application instance
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)


def get_rate_limit(endpoint_type: str) -> str:
    """
    Restituisce il limite rate per un tipo di endpoint.
    
    Uso con decoratore: @limiter.limit(get_rate_limit("login"))
    
    Args:
        endpoint_type: Chiave del dizionario RATE_LIMITS
            (es. "login", "gdpr_access", "create")
            
    Returns:
        Stringa limite (es. "5/minute") o default
    """
    return RATE_LIMITS.get(endpoint_type, DEFAULT_LIMIT)


async def check_rate_limit(request: Request, endpoint_type: str) -> None:
    """
    Verifica rate limit per endpoint (uso programmatico/dependency).
    
    Preferire il decoratore quando possibile:
    @limiter.limit(get_rate_limit("login"))
    
    Per uso come dependency: Depends con wrapper che passa endpoint_type.
    
    Args:
        request: FastAPI Request
        endpoint_type: Chiave RATE_LIMITS
        
    Raises:
        HTTPException: 429 se limite superato
    """
    try:
        from limits import parse
        from limits.strategies import FixedWindowRateLimiter
    except ImportError:
        # limits non disponibile - skip check (sviluppo senza slowapi)
        return

    storage = _get_manual_storage()
    if storage is None:
        return

    limit_str = get_rate_limit(endpoint_type)
    client_ip = get_remote_address(request)
    key = f"{endpoint_type}:{client_ip}"

    try:
        strategy = FixedWindowRateLimiter(storage)
        limit_item = parse(limit_str)

        if not strategy.hit(limit_item, key):
            logger.warning("Rate limit exceeded: type=%s IP=%s", endpoint_type, client_ip)
            raise HTTPException(
                status_code=429,
                detail="Troppe richieste. Riprova più tardi.",
                headers={"Retry-After": "60"},
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.debug("Rate limit check error (swallowed): %s", e)
        # Graceful: non bloccare l'app in caso di errore

"""
Security Headers Middleware
Aggiunge header HTTP di sicurezza secondo OWASP best practices.

Compliance:
- ISO 27001:2022 - A.14.1.2 (Securing application services)
- OWASP Top 10 - Security Headers
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware che aggiunge security headers a tutte le risposte HTTP.
    
    Headers implementati:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security: HSTS per HTTPS
    - Content-Security-Policy: CSP policy
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: feature policy
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Processa la richiesta e aggiunge security headers alla risposta.
        
        Args:
            request: FastAPI Request object
            call_next: Next middleware in chain
            
        Returns:
            Response con security headers aggiunti
        """
        try:
            # Processa la richiesta
            response = await call_next(request)
            
            # X-Content-Type-Options: Previene MIME type sniffing
            response.headers["X-Content-Type-Options"] = "nosniff"
            
            # X-Frame-Options: Previene clickjacking
            response.headers["X-Frame-Options"] = "DENY"
            
            # X-XSS-Protection: Abilita filtro XSS del browser
            response.headers["X-XSS-Protection"] = "1; mode=block"
            
            # Referrer-Policy: Controllo informazioni referrer
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            # Permissions-Policy: Disabilita feature non necessarie
            response.headers["Permissions-Policy"] = (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=()"
            )
            
            # Content-Security-Policy: Policy di sicurezza contenuti
            # NOTA: Policy permissiva per sviluppo, stringere in produzione
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "font-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
            
            # HSTS: Forza HTTPS (solo se la connessione è HTTPS)
            # max-age=31536000 = 1 anno
            if request.url.scheme == "https":
                response.headers["Strict-Transport-Security"] = (
                    "max-age=31536000; includeSubDomains"
                )
            
            return response
            
        except Exception as e:
            logger.error("Error in SecurityHeadersMiddleware: %s", e)
            raise


def get_security_headers_info() -> dict:
    """
    Ritorna informazioni sugli security headers implementati.
    
    Returns:
        dict: Dizionario con info su ogni header
    """
    return {
        "X-Content-Type-Options": {
            "value": "nosniff",
            "purpose": "Previene MIME type sniffing",
            "compliance": "OWASP A05:2021 - Security Misconfiguration"
        },
        "X-Frame-Options": {
            "value": "DENY",
            "purpose": "Previene clickjacking attacks",
            "compliance": "OWASP A01:2021 - Broken Access Control"
        },
        "X-XSS-Protection": {
            "value": "1; mode=block",
            "purpose": "Abilita filtro XSS del browser",
            "compliance": "OWASP A03:2021 - Injection"
        },
        "Referrer-Policy": {
            "value": "strict-origin-when-cross-origin",
            "purpose": "Controllo informazioni referrer",
            "compliance": "Privacy & Information Disclosure"
        },
        "Permissions-Policy": {
            "value": "geolocation=(), microphone=(), camera=(), ...",
            "purpose": "Disabilita API browser non necessarie",
            "compliance": "Principle of Least Privilege"
        },
        "Content-Security-Policy": {
            "value": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; ...",
            "purpose": "Previene XSS e data injection attacks",
            "compliance": "OWASP A03:2021 - Injection"
        },
        "Strict-Transport-Security": {
            "value": "max-age=31536000; includeSubDomains",
            "purpose": "Forza connessioni HTTPS",
            "compliance": "OWASP A02:2021 - Cryptographic Failures"
        }
    }

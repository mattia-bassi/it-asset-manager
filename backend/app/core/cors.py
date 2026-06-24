"""CORS origin list and helper to add CORS headers to responses (e.g. on 500 errors)."""
from fastapi import Request

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def get_cors_headers(request: Request) -> dict:
    """Return CORS headers for error responses so the frontend can read the body."""
    origin = request.headers.get("origin", "")
    headers = {}
    if origin in CORS_ORIGINS:
        headers["Access-Control-Allow-Origin"] = origin
    headers["Access-Control-Allow-Credentials"] = "true"
    return headers

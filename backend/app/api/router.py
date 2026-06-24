from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.routers import sites
from app.routers import people
from app.routers import asset_types
from app.routers import assets
from app.routers import inventory
from app.routers import assignments
from app.routers import document_templates
from app.routers import sims
from app.routers import badges
from app.routers import location_types
from app.routers import locations
from app.routers import reports
from app.routers import users
from app.routers import dashboard
from app.routers import audit_logs
from app.routers import gdpr
from app.routers import compliance
from app.routers import suppliers
from app.routers import documents

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(sites.router)
api_router.include_router(people.router)
api_router.include_router(asset_types.router)
api_router.include_router(assets.router)
api_router.include_router(inventory.router)
api_router.include_router(assignments.router)
api_router.include_router(dashboard.router, prefix="/dashboard")
api_router.include_router(document_templates.router)
api_router.include_router(sims.router)
api_router.include_router(badges.router)
api_router.include_router(location_types.router)
api_router.include_router(locations.router)
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(users.router)
api_router.include_router(audit_logs.router)
api_router.include_router(gdpr.router)
api_router.include_router(compliance.router)
api_router.include_router(suppliers.router)
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])

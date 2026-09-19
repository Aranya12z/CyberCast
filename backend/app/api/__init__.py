"""
app/api/__init__.py — Re-exports all FastAPI API routers.
"""
from app.api.auth import router as auth_router
from app.api.crimes import router as crimes_router
from app.api.atms import router as atms_router
from app.api.transactions import router as transactions_router
from app.api.predictions import router as predictions_router
from app.api.alerts import router as alerts_router
from app.api.dashboard import router as dashboard_router
from app.api.intelligence import router as intelligence_router

__all__ = [
    "auth_router",
    "crimes_router",
    "atms_router",
    "transactions_router",
    "predictions_router",
    "alerts_router",
    "dashboard_router",
    "intelligence_router",
]

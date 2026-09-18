"""
app/main.py — FastAPI application entrypoint with standard error envelope and router mounting.

CyberCast Backend API — AI-driven ATM withdrawal risk forecasting.
Reference: API_SPEC.md §Conventions (Standard error envelope)
"""
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import (
    alerts_router,
    atms_router,
    auth_router,
    crimes_router,
    dashboard_router,
    intelligence_router,
    predictions_router,
    transactions_router,
)
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="CyberCast API",
    version="0.1.0",
    description="CyberCast — AI-driven ATM withdrawal risk forecasting backend",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Standard Error Envelope Exception Handlers (API_SPEC.md §Conventions)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Standard error response format:
    { "error": { "code": "...", "message": "...", "details": {} } }
    """
    message = exc.detail if isinstance(exc.detail, str) else "HTTP Exception"
    details = exc.detail if isinstance(exc.detail, dict) else {}
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": message,
                "details": details,
            }
        },
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Malformed input handler returning 422 with standard error envelope.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Malformed request parameters or payload body.",
                "details": {"errors": exc.errors()},
            }
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catch-all internal server error handler.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred.",
                "details": {"error_type": type(exc).__name__},
            }
        },
    )


# Register all thin API routers under /api prefix
app.include_router(auth_router, prefix="/api")
app.include_router(crimes_router, prefix="/api")
app.include_router(atms_router, prefix="/api")
app.include_router(transactions_router, prefix="/api")
app.include_router(predictions_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(intelligence_router, prefix="/api")


@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": "CyberCast API", "env": settings.ENV}

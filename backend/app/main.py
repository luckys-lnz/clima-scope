"""
FastAPI Application Entry Point

Main application setup and configuration.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .utils.logging import get_logger

# Get logger
logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Meteorological Weather Report API for Kenya",
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    debug=settings.DEBUG,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
from .api.v1 import health, auth, reports, upload

app.include_router(health.router, prefix=f"{settings.API_V1_PREFIX}/health", tags=["health"])
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["authentication"])
app.include_router(reports.router, prefix=f"{settings.API_V1_PREFIX}/reports", tags=["reports"])
app.include_router(upload.router, prefix=f"{settings.API_V1_PREFIX}/uploads", tags=["upload"])

# Serve generated PDFs and other stored files
app.mount("/storage", StaticFiles(directory=settings.STORAGE_PATH), name="storage")


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("application_starting", version=settings.APP_VERSION)
    logger.info("database_url_configured", url=settings.SUPABASE_URL.split("@")[-1] if "@" in settings.SUPABASE_URL else "not_set")
    
    # Add auth initialization if needed
    logger.info("auth_initialized", provider="Supabase")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("application_shutting_down")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/api/docs",
        "api_prefix": settings.API_V1_PREFIX,
        "auth_endpoints": f"{settings.API_V1_PREFIX}/auth",
    }

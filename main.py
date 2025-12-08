"""
Email Assistant API - Main Application Entry Point
FastAPI application setup with all middleware and routes
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging
import uvicorn

from app.config import settings
from app import database
from app.routers import auth, emails, templates, settings_router, admin

logger = logging.getLogger(__name__)


# ============ Startup & Shutdown Events ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan - startup and shutdown
    """
    # Startup
    logger.info("🚀 Application starting up...")
    try:
        await database.connect_db()
        logger.info("✓ Database connected")
    except Exception as e:
        logger.error(f"✗ Failed to connect to database: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Application shutting down...")
    await database.disconnect_db()
    logger.info("✓ Database disconnected")


# ============ Application Initialization ============

app = FastAPI(
    title=settings.app_name,
    description="Email Assistant API with AI-powered email management",
    version=settings.app_version,
    openapi_url=f"{settings.api_prefix}/openapi.json",
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
    lifespan=lifespan
)


# ============ Middleware ============

# Trust proxy headers
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# ============ Exception Handlers ============

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.debug else "Internal server error"
        }
    )


# ============ Health Check Routes ============

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness check - verifies database connectivity"""
    try:
        # Quick database ping
        await database.db.command('ping')
        return {
            "status": "ready",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "database": "disconnected",
                "error": str(e)
            }
        )


# ============ Root Route ============

@app.get("/", tags=["Root"])
async def root():
    """Redirect to API docs"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"{settings.api_prefix}/docs")


# ============ Include Routers ============

# Authentication routes
app.include_router(
    auth.router,
    prefix=f"{settings.api_prefix}/auth",
    tags=["Authentication"],
    responses={
        400: {"description": "Bad Request"},
        401: {"description": "Unauthorized"},
        500: {"description": "Internal Server Error"}
    }
)

# Email routes
app.include_router(
    emails.router,
    prefix=f"{settings.api_prefix}/emails",
    tags=["Emails"]
)

# Templates routes
app.include_router(
    templates.router,
    prefix=f"{settings.api_prefix}/templates",
    tags=["Templates"]
)

# Settings routes
app.include_router(
    settings_router.router,
    prefix=f"{settings.api_prefix}/settings",
    tags=["Settings"]
)

# Admin routes
app.include_router(
    admin.router,
    prefix=f"{settings.api_prefix}/admin",
    tags=["Admin"]
)


# ============ Application Entry Point ============

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
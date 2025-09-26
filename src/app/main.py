"""
GPAlytics FastAPI Application
Main application entry point with router configuration
Migrated from app/main.py with updated import structure
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from ..shared.config import settings
from ..shared.database import init_db
from ..shared.health import router as health_router

# Import all routers
from ..routers.auth import router as auth_router
from ..routers.users import router as users_router
from ..routers.grades import router as grades_router
from ..routers.analytics import router as analytics_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events"""
    # Startup
    logger.info("🚀 Starting GPAlytics Backend...")
    try:
        await init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise
    
    logger.info("🌐 Server starting...")
    logger.info(f"📊 Environment: {settings.environment}")
    logger.info(f"🔧 Debug mode: {settings.debug}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down GPAlytics Backend...")


# Create FastAPI application with lifespan management
app = FastAPI(
    title="GPAlytics Backend API",
    description="Academic Performance Analytics & Grade Management System",
    version="2.0.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
    lifespan=lifespan,
)

# Configure CORS with default origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url),
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "status_code": 500,
            "path": str(request.url),
        }
    )

# Include routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(grades_router)
app.include_router(analytics_router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "GPAlytics Backend API",
        "version": "2.0.0",
        "status": "active",
        "environment": settings.environment,
        "docs": "/docs" if settings.environment == "development" else "disabled",
    }

# Development server entry point
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
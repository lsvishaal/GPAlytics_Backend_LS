"""
GPAlytics Backend - FastAPI Application
Clean, minimal FastAPI app for academic performance tracking
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .database import db_manager
from .auth import router as auth_router


logger = logging.getLogger(__name__)

# ==========================================
# APPLICATION LIFESPAN
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    # Startup
    logger.info("🚀 Starting GPAlytics Backend...")
    db_manager.initialize()
    await db_manager.create_tables()
    logger.info("✅ Database initialized")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down GPAlytics Backend...")
    await db_manager.close()
    logger.info("✅ Database connections closed")


# ==========================================
# FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title="GPAlytics Backend",
    description="Clean, minimal FastAPI backend for academic performance tracking",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(auth_router)


# ==========================================
# HEALTH CHECK ENDPOINTS
# ==========================================

@app.get("/health")
async def health_check():
    """Application health check"""
    return {"status": "healthy", "service": "GPAlytics Backend"}


@app.get("/health/db")
async def database_health_check():
    """Database health check"""
    is_healthy = await db_manager.health_check()
    if not is_healthy:
        raise HTTPException(status_code=503, detail="Database unhealthy")
    return {"status": "healthy", "database": "connected"}


# ==========================================
# ROOT ENDPOINT
# ==========================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to GPAlytics Backend",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

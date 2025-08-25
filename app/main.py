"""
GPAlytics Backend - FastAPI Application
Clean, minimal FastAPI app for academic performance tracking
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .database import db_manager, get_db_session
from .auth import register_user, login_user
from .models import UserRegister, UserLogin


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
# AUTHENTICATION ENDPOINTS
# ==========================================

@app.post("/auth/register")
async def register(user: UserRegister, db = Depends(get_db_session)):
    """Register a new user"""
    try:
        result = await register_user(db, user)
        return {"message": "User registered successfully", "user": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/auth/login")
async def login(user: UserLogin, db = Depends(get_db_session)):
    """Login user and return JWT token"""
    try:
        result = await login_user(db, user.regno, user.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


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

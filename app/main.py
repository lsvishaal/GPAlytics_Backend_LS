"""
GPAlytics Backend - FastAPI Application
Clean Architecture with Domain-Driven Design
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio

from .core import db_manager
from .core.health import readiness
from .auth import router as auth_router
from .grades import router as grades_router  
from .analytics import router as analytics_router
from .users import router as users_router

logger = logging.getLogger(__name__)

# ==========================================
# SERVERLESS DATABASE UTILITIES
# ==========================================

async def wait_for_serverless_db(max_retries: int = 5, base_delay: float = 2.0) -> bool:
    """
    Wait for Azure SQL Serverless database to wake up
    Implements exponential backoff for cold start scenarios
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"🔌 Attempting database connection (attempt {attempt + 1}/{max_retries})...")
            
            # Initialize database manager
            db_manager.initialize()
            logger.info("✅ Database manager initialized")
            
            # Try to create tables (this will test the actual connection)
            await db_manager.create_tables()
            logger.info("✅ Database tables created/verified")
            
            return True
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check if it's a serverless cold start related error
            if any(keyword in error_msg for keyword in ['timeout', 'not currently available', 'login timeout']):
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"⏳ Serverless database is starting up... waiting {delay}s (attempt {attempt + 1}/{max_retries})")
                logger.warning(f"   Error: {str(e)[:100]}...")
                
                if attempt < max_retries - 1:  # Don't sleep on the last attempt
                    await asyncio.sleep(delay)
                    continue
            else:
                # Different kind of error, log and continue to next attempt
                logger.warning(f"⚠️ Database connection error: {str(e)[:100]}...")
                if attempt < max_retries - 1:
                    await asyncio.sleep(base_delay)
                    continue
    
    logger.error("❌ Failed to connect to database after all retry attempts")
    return False

# ==========================================
# APPLICATION LIFESPAN
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown with serverless database support"""
    # Startup
    logger.info("🚀 Starting GPAlytics Backend...")
    
    # Optionally warm up DB at startup to reduce first-request latency.
    # Non-blocking by default (controlled via DB_WARMUP_ON_STARTUP=false).
    try:
        from .core.config import settings
        if settings.db_warmup_on_startup and settings.has_database_url:
            database_ready = await wait_for_serverless_db(max_retries=5, base_delay=3.0)
            if database_ready:
                logger.info("✅ Database fully initialized and ready")
            else:
                logger.warning("⚠️ Database warmup failed; continuing without blocking startup")
        else:
            logger.info("⏭️ Skipping DB warmup at startup (config disabled or no DATABASE_URL)")
    except Exception as e:
        logger.warning(f"⚠️ DB warmup skipped due to error: {e}")
    
    logger.info("✅ Application startup complete")
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down GPAlytics Backend...")
    try:
        await db_manager.close()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.warning(f"⚠️ Database close failed: {str(e)}")
    logger.info("✅ Shutdown complete")


# ==========================================
# FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title="GPAlytics Backend",
    description="Clean Architecture FastAPI backend for academic performance tracking and insights",
    version="2.0.0",
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

# Include domain routers
app.include_router(auth_router)
app.include_router(grades_router)
app.include_router(analytics_router)
app.include_router(users_router)


# ==========================================
# HEALTH CHECK ENDPOINTS (Ready-only)
# ==========================================

@app.get("/ready")
async def readiness_check():
    """Readiness probe: aggregates dependencies (DB, Redis, AI config).

    Returns 200 with full details even if unhealthy; status conveys readiness.
    """
    # Keep readiness quick and non-blocking
    result = await readiness(max_db_retries=1, base_delay=0.0)
    if result.get("status") != "healthy":
        # Keep 200 but include status; many orchestrators can parse JSON.
        # If you prefer strict semantics, you could return 503 here.
        return result
    return result

    # Single source of truth for health info; keep others out for simplicity


# ==========================================
# ROOT ENDPOINT
# ==========================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to GPAlytics Backend",
        "version": "2.0.0",
        "architecture": "Clean Architecture with Domain-Driven Design",
        "docs": "/docs",
        "ready": "/ready"
    }

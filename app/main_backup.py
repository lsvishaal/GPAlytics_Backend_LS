"""
GPAlytics Backend - FastAPI Application
Clean, minimal FastAPI app for academic performance tracking
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio

from .database import db_manager
from .auth import router as auth_router
from .OCR import router as grades_router
from .analytics import router as analytics_router
from .profile import router as profile_router


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
    
    # Try to connect to serverless database with retry logic
    database_ready = await wait_for_serverless_db(max_retries=5, base_delay=3.0)
    
    if database_ready:
        logger.info("✅ Database fully initialized and ready")
    else:
        logger.warning("⚠️ Database connection failed - running in development mode")
        logger.info("🔄 API endpoints will be available, but database operations will fail gracefully")
    
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

# Include routers
app.include_router(auth_router)
app.include_router(grades_router)
app.include_router(analytics_router)
app.include_router(profile_router)


# ==========================================
# HEALTH CHECK ENDPOINTS
# ==========================================

@app.get("/health")
async def health_check():
    """Application health check"""
    return {"status": "healthy", "service": "GPAlytics Backend"}


@app.get("/health/db")
async def database_health_check():
    """Database health check with serverless database support"""
    try:
        # First check if database manager is initialized
        if not db_manager._initialized:
            logger.warning("Database manager not initialized, attempting to initialize...")
            database_ready = await wait_for_serverless_db(max_retries=3, base_delay=2.0)
            if not database_ready:
                raise HTTPException(
                    status_code=503, 
                    detail="Database unavailable - serverless database may be starting up"
                )
        
        # Perform health check
        is_healthy = await db_manager.health_check()
        if not is_healthy:
            raise HTTPException(
                status_code=503, 
                detail="Database health check failed - may be in cold start"
            )
        
        return {"status": "healthy", "database": "connected", "type": "serverless"}
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        error_msg = str(e).lower()
        
        # Provide specific messages for serverless scenarios
        if any(keyword in error_msg for keyword in ['timeout', 'not currently available', 'login timeout']):
            raise HTTPException(
                status_code=503, 
                detail="Serverless database is starting up - please retry in a few seconds"
            )
        else:
            logger.error(f"Database health check error: {str(e)}")
            raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")


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

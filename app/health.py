"""
Health check and monitoring endpoints
Essential for production-ready APIs in 2025
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db_session
import time
import sys
from datetime import datetime

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    }

@router.get("/db")
async def database_health(db: AsyncSession = Depends(get_db_session)):
    """Database connectivity health check"""
    start_time = time.time()
    
    try:
        # Simple query to test database connectivity
        result = await db.execute(text("SELECT 1 as health_check"))
        query_time = round((time.time() - start_time) * 1000, 2)
        
        return {
            "status": "healthy",
            "database": "connected",
            "query_time_ms": query_time,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

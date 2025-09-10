"""
Core Database Configuration
Database connection and session management for Azure SQL
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine, async_sessionmaker
from sqlmodel import SQLModel
from sqlalchemy import text
from typing import AsyncGenerator
import logging

from .config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager for Azure SQL with serverless support"""
    
    def __init__(self):
        self.async_engine: AsyncEngine | None = None
        self.async_session_factory = None
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize Azure database connection"""
        if self._initialized:
            return
            
        logger.info(f"🔌 Connecting to Azure SQL Database ({settings.environment})...")
        
        # Engine configuration optimized for serverless Azure SQL
        engine_kwargs = {
            "echo": settings.debug and settings.is_development,
            "pool_size": 5,
            "pool_timeout": 30,
            "pool_pre_ping": False,  # Disable pre_ping for aioodbc compatibility
            "pool_recycle": 3600,  # Recycle connections every hour
        }
        
        self.async_engine = create_async_engine(
            settings.database_url_str,
            **engine_kwargs
        )
        
        # Create proper async session factory for FastAPI DI
        self.async_session_factory = async_sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        self._initialized = True
        logger.info("✅ Azure SQL Database connected")
    
    async def create_tables(self) -> None:
        """Create database tables"""
        if not self.async_engine:
            raise RuntimeError("Database not initialized")
        
        logger.info("🏗️ Creating tables...")
        async with self.async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("✅ Tables created")
    
    async def health_check(self) -> bool:
        """Check database health"""
        if not self.async_engine:
            return False
        
        try:
            async with self.async_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close database connections"""
        if self.async_engine:
            await self.async_engine.dispose()
            self._initialized = False


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for FastAPI dependency injection"""
    if not db_manager._initialized:
        db_manager.initialize()
    
    if not db_manager.async_session_factory:
        raise RuntimeError("Database session factory not initialized")
    
    # Use the proper async session context manager
    session = db_manager.async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

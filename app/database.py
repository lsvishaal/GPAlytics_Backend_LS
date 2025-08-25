"""
Database connection and configuration
"""
from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlalchemy import text
import logging
import secrets

logger = logging.getLogger(__name__)

# ==========================================
# CONFIGURATION
# ==========================================

class Settings(BaseSettings):
    """Application settings"""
    database_url: SecretStr = Field(...)
    jwt_secret_key: SecretStr = Field(default_factory=lambda: SecretStr(secrets.token_urlsafe(32)))
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    debug: bool = True
    
    @property
    def database_url_str(self) -> str:
        return self.database_url.get_secret_value()
    
    @property 
    def jwt_secret_str(self) -> str:
        return self.jwt_secret_key.get_secret_value()

    class Config:
        env_file = ".env"

settings = Settings()

# ==========================================
# DATABASE MANAGER
# ==========================================

class DatabaseManager:
    """Database connection manager"""
    
    def __init__(self):
        self.async_engine = None
        self.async_session_factory = None
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize database connection"""
        if self._initialized:
            return
            
        logger.info("🔌 Initializing database...")
        
        self.async_engine = create_async_engine(
            settings.database_url_str,
            echo=settings.debug,
            pool_size=5,
            pool_timeout=30,
            pool_pre_ping=True
        )
        
        self.async_session_factory = sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        self._initialized = True
        logger.info("✅ Database initialized")
    
    async def create_tables(self) -> None:
        """Create database tables"""
        logger.info("🏗️ Creating tables...")
        async with self.async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("✅ Tables created")
    
    async def health_check(self) -> bool:
        """Check database health"""
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

db_manager = DatabaseManager()

async def get_db_session() -> AsyncSession:
    """Get database session for FastAPI"""
    async with db_manager.async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

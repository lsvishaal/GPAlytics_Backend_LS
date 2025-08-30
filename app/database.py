"""
 database connection for Azure SQL Database
"""
from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlalchemy import text
from typing import AsyncGenerator
import logging
import secrets

logger = logging.getLogger(__name__)

# ==========================================
# SETTINGS
# ==========================================

class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: SecretStr = Field(...)
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379")
    
    # JWT
    jwt_secret_key: SecretStr = Field(default_factory=lambda: SecretStr(secrets.token_urlsafe(32)))
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    # App
    debug: bool = False
    environment: str = Field(default="production")
    
    @property
    def database_url_str(self) -> str:
        """Get database URL - automatically uses test database during testing"""
        url = self.database_url.get_secret_value()
        
        # Auto-switch to test database if we're in test mode
        if self.environment.lower() == "testing":
            # Replace database name with test version
            if "database=" in url:
                # For Azure SQL: replace database name
                import re
                url = re.sub(r'database=([^;]+)', r'database=\1_test', url)
            else:
                # For other databases, append _test
                url = url.rstrip('/') + '_test'
        
        return url
    
    @property 
    def jwt_secret_str(self) -> str:
        return self.jwt_secret_key.get_secret_value()
    
    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"

    model_config = {"env_file": ".env"}

settings = Settings()

# ==========================================
# DATABASE MANAGER
# ==========================================

class DatabaseManager:
    """Simple database manager for Azure SQL"""
    
    def __init__(self):
        self.async_engine = None
        self.async_session_factory = None
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize Azure database connection"""
        if self._initialized:
            return
            
        logger.info(f"🔌 Connecting to Azure SQL Database ({settings.environment})...")
        
        # Engine configuration
        engine_kwargs = {
            "echo": settings.debug and settings.is_development,
            "pool_size": 5,
            "pool_timeout": 30,
            "pool_pre_ping": True,
            "pool_recycle": 3600,  # Recycle connections every hour
        }
        
        self.async_engine = create_async_engine(
            settings.database_url_str,
            **engine_kwargs
        )
        
        self.async_session_factory = sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        self._initialized = True
        logger.info("✅ Azure SQL Database connected")
    
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

# Global database manager
db_manager = DatabaseManager()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for FastAPI dependency injection"""
    if not db_manager._initialized:
        db_manager.initialize()
    
    async with db_manager.async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

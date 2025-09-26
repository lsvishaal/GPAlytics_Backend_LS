"""
Core Database Configuration
Database connection and session management for Azure SQL
"""
import logging
from typing import Callable, cast, AsyncGenerator
from urllib.parse import quote_plus

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
try:  # SQLAlchemy 2.0+
    from sqlalchemy.ext.asyncio import async_sessionmaker as _async_sessionmaker  # type: ignore[attr-defined]
    _HAS_ASYNC_SESSIONMAKER = True
except Exception:  # SQLAlchemy 1.4 fallback
    _HAS_ASYNC_SESSIONMAKER = False
    from sqlalchemy.orm import sessionmaker as _sync_sessionmaker  # type: ignore

from sqlalchemy import text
from sqlmodel import SQLModel

from .config import settings

logger = logging.getLogger(__name__)


def _make_session_factory(engine: AsyncEngine) -> Callable[[], AsyncSession]:
    """Create a factory that returns AsyncSession instances across SA versions."""
    if _HAS_ASYNC_SESSIONMAKER:
        factory = _async_sessionmaker(engine, expire_on_commit=False)  # type: ignore[misc]
        # factory() -> AsyncSession
        return cast(Callable[[], AsyncSession], factory)
    # Fallback using ORM sessionmaker with AsyncSession class
    factory = _sync_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[misc]
    return cast(Callable[[], AsyncSession], factory)


def build_sqlalchemy_url(raw: str) -> str:
    """Normalize DATABASE_URL to a SQLAlchemy async URL.

    Supports two forms:
    - Full SQLAlchemy URL (e.g., "mssql+aioodbc://...") -> returned as-is
    - Raw ODBC connection string (e.g., "Driver=ODBC Driver 18 for SQL Server;Server=tcp:...;")
      -> wrapped as "mssql+aioodbc:///?odbc_connect=<urlencoded>"
    """
    s = (raw or "").strip()
    if not s:
        return s
    # Heuristic: if it looks like a URL with scheme, keep as-is
    if "://" in s:
        # ensure async variant for MSSQL
        lower = s.lower()
        if lower.startswith("mssql+"):
            if "+pyodbc" in lower:
                return s.replace("+pyodbc", "+aioodbc")
            # if driver unspecified like mssql://, prefer aioodbc
            if s.lower().startswith("mssql://"):
                return s.replace("mssql://", "mssql+aioodbc://", 1)
        return s
    # Otherwise assume it's a raw ODBC connect string
    return f"mssql+aioodbc:///?odbc_connect={quote_plus(s)}"


class DatabaseManager:
    """Database manager for Azure SQL with serverless support.

    Behavior:
    - If `DATABASE_URL` is missing/empty, initialization is skipped and health_check returns False.
    - Engine/session creation occurs lazily and once; callers can check `_initialized`.
    """
    
    def __init__(self):
        self.async_engine: AsyncEngine | None = None
        self.async_session_factory = None
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize Azure database connection if configuration is present.

        This function is safe to call multiple times. If DATABASE_URL is not set,
        the manager remains uninitialized so the app can still boot (readiness
        will report DB as unhealthy or skipped based on usage).
        """
        if self._initialized:
            return
        
        if not settings.has_database_url:
            logger.warning("DATABASE_URL not configured; skipping DB initialization")
            return
        
        logger.info(f"🔌 Connecting to Azure SQL Database ({settings.environment})...")
        
        # Engine configuration optimized for serverless Azure SQL; adapt for sqlite
        sqlalchemy_url = build_sqlalchemy_url(settings.database_url_str)
        lower_url = sqlalchemy_url.lower()
        if lower_url.startswith("sqlite"):
            engine_kwargs = {
                "echo": settings.debug and settings.is_development,
            }
        else:
            engine_kwargs = {
                "echo": settings.debug and settings.is_development,
                "pool_size": 5,
                "pool_timeout": 30,
                "pool_pre_ping": False,  # Disable pre_ping for aioodbc compatibility
                "pool_recycle": 3600,  # Recycle connections every hour
            }
        
        self.async_engine = create_async_engine(sqlalchemy_url, **engine_kwargs)
        
        # Create proper async session factory for FastAPI DI
        self.async_session_factory = _make_session_factory(self.async_engine)
        
        self._initialized = True
        logger.info("✅ Azure SQL Database connected")
    
    async def create_tables(self) -> None:
        """Create database tables"""
        if not self.async_engine:
            logger.warning("create_tables called before DB initialization; skipping")
            return
        
        logger.info("🏗️ Creating tables...")
        async with self.async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("✅ Tables created")
    
    async def health_check(self) -> bool:
        """Check database health"""
        if not self.async_engine:
            # Not initialized or no DATABASE_URL
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
        # Always reset flags so init can happen again later if config changes
        self.async_engine = None
        self.async_session_factory = None
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


async def init_db() -> None:
    """Initialize database and create tables"""
    if not db_manager._initialized:
        db_manager.initialize()
    await db_manager.create_tables()
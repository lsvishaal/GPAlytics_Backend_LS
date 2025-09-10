"""
Database Connection Test
Test Azure SQL connection independently
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_connection():
    """Test database connection step by step"""
    
    # Import settings
    try:
        from app.core.config import settings
        logger.info("✅ Settings imported successfully")
        logger.info(f"Database URL present: {bool(settings.database_url_str)}")
        logger.info(f"Database URL starts with: {settings.database_url_str[:20]}...")
    except Exception as e:
        logger.error(f"❌ Failed to import settings: {e}")
        return False
    
    # Test engine creation
    try:
        logger.info("🔧 Creating database engine...")
        engine = create_async_engine(
            settings.database_url_str,
            echo=True,
            pool_timeout=10,  # Shorter timeout for testing
            pool_pre_ping=True
        )
        logger.info("✅ Database engine created")
    except Exception as e:
        logger.error(f"❌ Failed to create engine: {e}")
        return False
    
    # Test connection
    try:
        logger.info("🔌 Testing database connection...")
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as test_value"))
            row = result.fetchone()
            logger.info(f"✅ Database connection successful! Result: {row}")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False
    finally:
        try:
            await engine.dispose()
            logger.info("✅ Engine disposed successfully")
        except Exception as e:
            logger.warning(f"⚠️ Engine disposal warning: {e}")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_database_connection())
    if success:
        logger.info("🎉 All database tests passed!")
        sys.exit(0)
    else:
        logger.error("💥 Database tests failed!")
        sys.exit(1)

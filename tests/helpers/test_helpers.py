"""
Test helper functions - Professional testing utilities
"""
import asyncio
from sqlalchemy import text
from app.database import db_manager

async def cleanup_test_users():
    """
    Clean up test users safely
    Only removes users with test patterns, preserves real data
    """
    test_patterns = ['AB%', 'CD%', 'EF%', 'GH%', 'IJ%']
    
    try:
        db_manager.initialize()
        async with db_manager.async_session_factory() as db:
            # Build safe WHERE clause
            where_conditions = " OR ".join([f"regno LIKE '{pattern}'" for pattern in test_patterns])
            sql_query = text(f"DELETE FROM users WHERE {where_conditions}")
            
            result = await db.execute(sql_query)
            await db.commit()
            print(f"🧹 Cleaned {result.rowcount} test users")
            return result.rowcount
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")
        return 0

def clean_test_data_sync():
    """Synchronous wrapper for async cleanup"""
    return asyncio.run(cleanup_test_users())

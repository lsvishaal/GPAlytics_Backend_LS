"""
Pytest configuration for GPAlytics Backend tests
Cloud-first testing: Uses same Azure SQL Database as production
"""

import pytest
import asyncio
from pathlib import Path
import sys
import os

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment
os.environ["ENVIRONMENT"] = "testing"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def setup_test_db():
    """Setup test database before each test
    
    Note: Uses same Azure SQL Database as production.
    Tests should be designed to be non-destructive.
    """
    from app.database import db_manager
    
    # Initialize Azure database connection for tests
    db_manager.initialize()
    
    # Ensure tables exist (idempotent operation)
    await db_manager.create_tables()
    
    yield
    
\

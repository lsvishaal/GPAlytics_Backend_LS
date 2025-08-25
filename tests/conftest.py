"""
Pytest configuration for GPAlytics Backend tests
"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def setup_test_db():
    """Setup test database before each test"""
    from app.database import db_manager
    
    # Initialize database for tests
    db_manager.initialize()
    await db_manager.create_tables()
    
    yield
    
    # Cleanup after test (optional)

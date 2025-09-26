"""Pytest configuration and shared fixtures"""
import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from src.app.main import app
from src.shared.database import get_db_session, db_manager
from src.shared.entities import User
from src.shared.security import hash_password


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """Setup test database"""
    # Initialize database manager
    db_manager.initialize()
    
    # Create tables if they don't exist
    await db_manager.create_tables()
    
    yield
    
    # Cleanup after tests
    await db_manager.close()


@pytest.fixture
async def db_session(setup_database) -> AsyncSession:
    """Get database session for tests"""
    async for session in get_db_session():
        yield session
        await session.rollback()  # Rollback any changes
        await session.close()


@pytest.fixture
async def client(setup_database) -> AsyncClient:
    """Get HTTP client for API tests"""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user for authentication tests"""
    user = User(
        name="Test User",
        regno="RA2211027099999",
        password_hash=hash_password("testpass123"),
        batch=2022
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """Get authentication headers with valid JWT token"""
    login_data = {
        "regno": test_user.regno,
        "password": "testpass123",
        "remember_me": False,
        "use_cookies": False
    }
    
    response = await client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    return {"Authorization": f"Bearer {token_data['access_token']}"}

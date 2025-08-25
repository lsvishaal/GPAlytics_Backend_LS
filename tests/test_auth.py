"""
GPAlytics Backend Tests
Consolidated authentication tests
"""

import pytest
import logging
import os
from app.auth import register_user, login_user
from app.models import UserRegister
from app.database import db_manager

# Setup logging for tests
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'test_errors.log')

logging.basicConfig(
    filename=LOG_FILE, 
    level=logging.ERROR, 
    format='%(asctime)s %(levelname)s %(message)s'
)

def log_error(error, description):
    """Log test errors"""
    logging.error(f"{error} | {description}")

@pytest.mark.asyncio
async def test_user_registration():
    """Test successful user registration"""
    db_manager.initialize()
    await db_manager.create_tables()
    
    user = UserRegister(
        name="Test User", 
        regno="RA2211027020100", 
        password="TestPass123!", 
        batch=2022
    )
    
    async with db_manager.async_session_factory() as db:
        try:
            result = await register_user(db, user)
            assert result is not None
            assert "User registered successfully" in str(result)
        except Exception as e:
            log_error(e, "User registration test failed")
            if "already exists" not in str(e):  # Allow existing user
                pytest.fail(f"Registration failed: {e}")

@pytest.mark.asyncio
async def test_duplicate_registration():
    """Test duplicate registration prevention"""
    db_manager.initialize()
    await db_manager.create_tables()
    
    user = UserRegister(
        name="Duplicate User", 
        regno="RA2211027020101", 
        password="TestPass123!", 
        batch=2022
    )
    
    async with db_manager.async_session_factory() as db:
        try:
            # First registration
            await register_user(db, user)
        except Exception:
            pass  # Ignore if already exists
        
        # Second registration should fail
        try:
            await register_user(db, user)
            pytest.fail("Duplicate registration should fail")
        except ValueError as e:
            assert "already exists" in str(e)
        except Exception as e:
            log_error(e, "Unexpected error in duplicate registration test")
            pytest.fail(f"Unexpected error: {e}")

@pytest.mark.asyncio
async def test_password_validation():
    """Test password strength validation"""
    db_manager.initialize()
    await db_manager.create_tables()
    
    weak_user = UserRegister(
        name="Weak Password User", 
        regno="RA2211027020102", 
        password="weak", 
        batch=2022
    )
    
    async with db_manager.async_session_factory() as db:
        try:
            await register_user(db, weak_user)
            pytest.fail("Weak password should be rejected")
        except ValueError as e:
            assert "Password" in str(e)
        except Exception as e:
            log_error(e, "Unexpected error in password validation test")
            pytest.fail(f"Unexpected error: {e}")

@pytest.mark.asyncio
async def test_invalid_login():
    """Test login with wrong credentials"""
    db_manager.initialize()
    await db_manager.create_tables()
    
    user = UserRegister(
        name="Login Test User", 
        regno="RA2211027020103", 
        password="TestPass123!", 
        batch=2022
    )
    
    async with db_manager.async_session_factory() as db:
        try:
            # Register user first
            await register_user(db, user)
        except Exception:
            pass  # Ignore if already exists
        
        # Try login with wrong password
        try:
            await login_user(db, user.regno, "WrongPassword!")
            pytest.fail("Login with wrong password should fail")
        except ValueError as e:
            assert "Invalid credentials" in str(e)
        except Exception as e:
            log_error(e, "Unexpected error in invalid login test")
            pytest.fail(f"Unexpected error: {e}")

@pytest.mark.asyncio
async def test_regno_format_validation():
    """Test registration number format validation"""
    db_manager.initialize()
    await db_manager.create_tables()
    
    invalid_user = UserRegister(
        name="Invalid Regno User", 
        regno="INVALID_REGNO", 
        password="TestPass123!", 
        batch=2022
    )
    
    async with db_manager.async_session_factory() as db:
        try:
            await register_user(db, invalid_user)
            pytest.fail("Invalid regno format should be rejected")
        except ValueError as e:
            assert "Registration number" in str(e)
        except Exception as e:
            log_error(e, "Unexpected error in regno validation test")
            pytest.fail(f"Unexpected error: {e}")

@pytest.mark.asyncio
async def test_successful_login():
    """Test successful login flow"""
    db_manager.initialize()
    await db_manager.create_tables()
    
    user = UserRegister(
        name="Login Success User", 
        regno="RA2211027020104", 
        password="TestPass123!", 
        batch=2022
    )
    
    async with db_manager.async_session_factory() as db:
        try:
            # Register user first
            await register_user(db, user)
        except Exception:
            pass  # Ignore if already exists
        
        # Login with correct credentials
        try:
            result = await login_user(db, user.regno, user.password)
            assert result is not None
            assert "access_token" in result
        except Exception as e:
            log_error(e, "Successful login test failed")
            pytest.fail(f"Login failed: {e}")

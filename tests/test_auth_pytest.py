import pytest
import logging
import os
from ..app.auth import register_user, login_user
from ..app.models import UserRegister
from ..app.database import db_manager

LOG_FILE = os.path.join(os.path.dirname(__file__), 'logs', 'auth_test_errors.log')
logging.basicConfig(filename=LOG_FILE, level=logging.ERROR, format='%(asctime)s %(levelname)s %(message)s')

def log_error(error, desc):
    logging.error(f"{error} | {desc}")

@pytest.mark.asyncio
async def test_duplicate_registration():
    db_manager.initialize()
    await db_manager.create_tables()
    user = UserRegister(name="Test User", regno="RA2211027020113", password="TestPass123!", batch=2022)
    async with db_manager.async_session_factory() as db:
        try:
            await register_user(db, user)
        except Exception as e:
            pass  # Ignore if already exists
        try:
            await register_user(db, user)
            assert False, "Duplicate registration should fail"
        except ValueError as e:
            assert "already exists" in str(e)
        except Exception as e:
            log_error(e, "Unexpected error on duplicate registration")
            assert False

@pytest.mark.asyncio
async def test_password_strength():
    weak_user = UserRegister(name="Weak User", regno="RA2211027020114", password="weak", batch=2022)
    db_manager.initialize()
    await db_manager.create_tables()
    async with db_manager.async_session_factory() as db:
        try:
            await register_user(db, weak_user)
            assert False, "Weak password should not be accepted"
        except ValueError as e:
            assert "Password" in str(e)
        except Exception as e:
            log_error(e, "Unexpected error on password strength test")
            assert False

@pytest.mark.asyncio
async def test_invalid_login():
    db_manager.initialize()
    await db_manager.create_tables()
    user = UserRegister(name="Test User", regno="RA2211027020115", password="TestPass123!", batch=2022)
    async with db_manager.async_session_factory() as db:
        try:
            await register_user(db, user)
        except Exception:
            pass
        try:
            await login_user(db, user.regno, "WrongPassword!")
            assert False, "Login with wrong password should fail"
        except ValueError as e:
            assert "Invalid credentials" in str(e)
        except Exception as e:
            log_error(e, "Unexpected error on invalid login")
            assert False

@pytest.mark.asyncio
async def test_invalid_regno_format():
    db_manager.initialize()
    await db_manager.create_tables()
    bad_user = UserRegister(name="Bad User", regno="BADREGNO", password="TestPass123!", batch=2022)
    async with db_manager.async_session_factory() as db:
        try:
            await register_user(db, bad_user)
            assert False, "Invalid regno format should not be accepted"
        except ValueError as e:
            assert "Registration number" in str(e)
        except Exception as e:
            log_error(e, "Unexpected error on regno format test")
            assert False

@pytest.mark.asyncio
async def test_sql_injection():
    db_manager.initialize()
    await db_manager.create_tables()
    inj_user = UserRegister(name="Inject User", regno="RA2211027020116", password="'; DROP TABLE users;--", batch=2022)
    async with db_manager.async_session_factory() as db:
        try:
            await register_user(db, inj_user)
            assert False, "SQL injection password should not be accepted"
        except ValueError as e:
            assert "Password" in str(e) or "Invalid" in str(e)
        except Exception as e:
            log_error(e, "Unexpected error on SQL injection test")
            assert False

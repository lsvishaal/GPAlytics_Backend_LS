"""
Authentication for GPAlytics MVP
"""
from typing import Optional
import re
import logging
from datetime import datetime, timezone, timedelta
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from .models import User, UserRegister, UserLogin, UserPublic, Token
from .database import get_db_session, settings

logger = logging.getLogger(__name__)
pwd_context = PasswordHasher()
security = HTTPBearer()

# ==========================================
# UTILITIES
# ==========================================

def hash_password(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    try:
        pwd_context.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False

def create_access_token(data: dict) -> str:
    """Create JWT token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_str, algorithm=settings.jwt_algorithm)

# ==========================================
# VALIDATION
# ==========================================

def validate_regno(regno: str) -> Optional[str]:
    """Validate registration number"""
    if len(regno) != 15:
        return "Registration number must be 15 characters"
    if not regno[:2].isalpha() or not regno[:2].isupper():
        return "First 2 characters must be uppercase letters"
    if not regno[2:].isdigit():
        return "Last 13 characters must be digits"
    return None

def validate_password(password: str) -> Optional[str]:
    """Validate password"""
    if len(password) < 8:
        return "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return "Password must contain uppercase letter"
    if not any(c.islower() for c in password):
        return "Password must contain lowercase letter"
    if not any(c.isdigit() for c in password):
        return "Password must contain digit"
    if not any(not c.isalnum() for c in password):
        return "Password must contain special character"
    return None

# ==========================================
# DATABASE OPERATIONS
# ==========================================

async def get_user_by_regno(db: AsyncSession, regno: str) -> Optional[User]:
    """Get user by registration number"""
    try:
        statement = select(User).where(User.regno == regno.upper())
        result = await db.execute(statement)
        return result.scalar_one_or_none()
    except Exception:
        return None

async def register_user(db: AsyncSession, user_data: UserRegister) -> dict:
    """Register new user"""
    
    # Validate
    if error := validate_regno(user_data.regno):
        raise ValueError(error)
    if error := validate_password(user_data.password):
        raise ValueError(error)
    
    # Check if exists
    if await get_user_by_regno(db, user_data.regno):
        raise ValueError("User already exists")
    
    # Create user
    db_user = User(
        name=user_data.name.strip(),
        regno=user_data.regno.upper(),
        batch=user_data.batch,
        password_hash=hash_password(user_data.password)
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    # Create token
    token_data = {
        "sub": db_user.id,
        "regno": db_user.regno,
        "name": db_user.name,
        "batch": db_user.batch
    }
    access_token = create_access_token(token_data)
    
    return {
        "user": UserPublic(
            id=db_user.id,
            name=db_user.name,
            regno=db_user.regno,
            batch=db_user.batch,
            created_at=db_user.created_at,
            last_login=db_user.last_login
        ),
        "token": Token(
            access_token=access_token,
            expires_in=settings.jwt_expire_minutes * 60
        )
    }

async def login_user(db: AsyncSession, regno: str, password: str) -> dict:
    """Login user"""
    
    user = await get_user_by_regno(db, regno)
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Invalid credentials")
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    
    # Create token
    token_data = {
        "sub": user.id,
        "regno": user.regno,
        "name": user.name,
        "batch": user.batch
    }
    access_token = create_access_token(token_data)
    
    return {
        "user": UserPublic(
            id=user.id,
            name=user.name,
            regno=user.regno,
            batch=user.batch,
            created_at=user.created_at,
            last_login=user.last_login
        ),
        "token": Token(
            access_token=access_token,
            expires_in=settings.jwt_expire_minutes * 60
        )
    }

# ==========================================
# FASTAPI ROUTES
# ==========================================

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db_session)):
    """Register new user"""
    try:
        result = await register_user(db, user_data)
        return {"message": "Registration successful", **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db_session)):
    """Login user"""
    try:
        result = await login_user(db, credentials.regno, credentials.password)
        return {"message": "Login successful", **result}
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

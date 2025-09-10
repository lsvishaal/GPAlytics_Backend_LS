"""
User Entity Models
Database models and Pydantic schemas for user domain
"""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid


# ==========================================
# DATABASE TABLE MODELS
# ==========================================

class UserBase(SQLModel):
    """Shared user fields"""
    name: str = Field(max_length=100)
    regno: str = Field(unique=True, index=True, max_length=15, min_length=15)
    batch: int = Field(ge=2015, le=2045)


class User(UserBase, table=True):
    """User database table"""
    __tablename__ = "users"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    password_hash: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)
    last_login: Optional[datetime] = Field(default=None)


# ==========================================
# API SCHEMA MODELS
# ==========================================

class UserRegisterSchema(SQLModel):
    """User registration request schema"""
    name: str = Field(min_length=1, max_length=100)
    regno: str = Field(min_length=15, max_length=15)
    password: str = Field(min_length=8, max_length=100)
    batch: int = Field(ge=2015, le=2045)


class UserLoginSchema(SQLModel):
    """User login request schema"""
    regno: str = Field(max_length=15)
    password: str = Field(max_length=100)


class UserPublicSchema(UserBase):
    """Public user data (no sensitive info)"""
    id: str
    created_at: datetime
    last_login: Optional[datetime]


class TokenSchema(SQLModel):
    """JWT token response schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ForgotPasswordSchema(SQLModel):
    """Forgot password request schema"""
    regno: str = Field(max_length=15)
    name: str = Field(min_length=1, max_length=100)
    new_password: str = Field(min_length=8, max_length=100)

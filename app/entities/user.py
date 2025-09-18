"""
User Entity Models
Database models and Pydantic schemas for user domain
"""
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
import uuid

if TYPE_CHECKING:
    from .refresh_token import RefreshToken


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
    
    # Relationship to RefreshTokens
    refresh_tokens: list["RefreshToken"] = Relationship(back_populates="user")


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
    remember_me: bool = Field(default=False, description="Keep user logged in for extended period (7 days)")
    use_cookies: bool = Field(default=False, description="Store tokens as HttpOnly cookies for enhanced security")


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

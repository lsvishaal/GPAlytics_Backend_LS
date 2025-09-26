"""
Refresh Token Entity Models
Database models for refresh token management
"""
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from .user import User


class RefreshToken(SQLModel, table=True):
    """Refresh token database table for secure session management"""
    __tablename__ = "refresh_tokens"
    
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), 
        primary_key=True, 
        max_length=36
    )
    user_id: str = Field(
        foreign_key="users.id", 
        index=True, 
        max_length=36
    )
    token_hash: str = Field(
        unique=True, 
        index=True, 
        max_length=255,
        description="Hashed refresh token for security"
    )
    expires_at: datetime = Field(
        index=True,
        description="Token expiration timestamp"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Token creation timestamp"
    )
    is_revoked: bool = Field(
        default=False,
        description="Whether token has been revoked"
    )
    
    # Relationship to User
    user: Optional["User"] = Relationship(back_populates="refresh_tokens")


class RefreshTokenCreate(SQLModel):
    """Schema for creating refresh tokens"""
    user_id: str
    expires_at: datetime


class RefreshTokenResponse(SQLModel):
    """Schema for refresh token responses"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
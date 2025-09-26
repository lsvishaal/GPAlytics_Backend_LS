"""
SQLModel database models for GPAlytics MVP
Clean and simple models
"""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid

# ==========================================
# USER AUTHENTICATION MODELS
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
# API MODELS
# ==========================================

class UserRegister(SQLModel):
    """User registration request"""
    name: str = Field(min_length=1, max_length=100)
    regno: str = Field(min_length=15, max_length=15)
    password: str = Field(min_length=8, max_length=100)
    batch: int = Field(ge=2015, le=2045)

class UserLogin(SQLModel):
    """User login request"""
    regno: str = Field(max_length=15)
    password: str = Field(max_length=100)

class UserPublic(UserBase):
    """Public user data (no sensitive info)"""
    id: str
    created_at: datetime
    last_login: Optional[datetime]

class Token(SQLModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

# ==========================================
# GRADE & UPLOAD MODELS
# ==========================================

class Grade(SQLModel, table=True):
    """
    Grade Database Table
    """
    __tablename__ = "grades"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    user_id: str = Field(foreign_key="users.id", max_length=36)
    course_name: str = Field(max_length=200)
    course_code: str = Field(max_length=20)
    credits: int = Field(ge=1, le=6)
    grade: str = Field(max_length=5)
    semester: int = Field(ge=1, le=12)
    gpa_points: float = Field(ge=0.0, le=10.0) # Using 10 for grade points like O=10
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GradeUpload(SQLModel, table=True):
    """Tracks file uploads for processing"""
    __tablename__ = "grade_uploads"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    user_id: str = Field(foreign_key="users.id", max_length=36)
    filename: str = Field(max_length=255)
    status: str = Field(default="processing", max_length=50) # e.g., processing, completed, failed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UploadStatusResponse(SQLModel):
    """Response model after a file is uploaded"""
    upload_id: str
    filename: str
    status: str
    message: str = "File received and is being processed."

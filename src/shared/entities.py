"""
Entity Models - Database and API Schemas
Combined entity models for all domains (users, grades, tokens)
"""
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime, timezone
import uuid

# ==========================================
# USER ENTITIES
# ==========================================

class UserBase(SQLModel):
    """Shared user fields"""
    name: str = Field(max_length=100)
    regno: str = Field(unique=True, index=True, max_length=15, min_length=15)
    batch: int = Field(ge=2015, le=2045)


class User(UserBase, table=True):
    """User database table"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    password_hash: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)
    last_login: Optional[datetime] = Field(default=None)
    
    # Relationship to RefreshTokens
    refresh_tokens: list["RefreshToken"] = Relationship(back_populates="user")


class UserRegisterSchema(SQLModel):
    """
    👤 **User Registration Schema**
    
    Data model for new user registration with comprehensive validation.
    
    **Field Requirements:**
    - `name`: Student's full name (1-100 chars)
    - `regno`: Registration number (exactly 15 chars, format: RA2211027020XXX)
    - `password`: Plain text password (8-100 chars, will be hashed)
    - `batch`: Academic batch year (2015-2045)
    
    **Example:**
    ```json
    {
        "name": "Alice Johnson",
        "regno": "RA2211027020001",
        "password": "SecurePass123!",
        "batch": 2022
    }
    ```
    """
    name: str = Field(
        min_length=1, 
        max_length=100,
        description="Student's full name as per official records"
    )
    regno: str = Field(
        min_length=15, 
        max_length=15,
        description="Unique 15-character registration number (format: RA2211027020XXX)"
    )
    password: str = Field(
        min_length=8, 
        max_length=100,
        description="Plain text password (min 8 chars, will be securely hashed)"
    )
    batch: int = Field(
        ge=2015, 
        le=2045,
        description="Academic batch/admission year (must be between 2015-2045)"
    )


class UserLoginSchema(SQLModel):
    """
    🔑 **User Login Schema**
    
    Authentication data model with session management options.
    
    **Field Details:**
    - `regno`: Registration number for identification
    - `password`: Plain text password for verification
    - `remember_me`: Extends session to 7 days (default: 30 minutes)
    - `use_cookies`: Store tokens as HttpOnly cookies for enhanced security
    
    **Example:**
    ```json
    {
        "regno": "RA2211027020113",
        "password": "Welcome3#",
        "remember_me": true,
        "use_cookies": false
    }
    ```
    """
    regno: str = Field(
        max_length=15,
        description="Student registration number (15 characters)"
    )
    password: str = Field(
        max_length=100,
        description="User password (plain text, will be verified against hash)"
    )
    remember_me: bool = Field(
        default=False, 
        description="Keep user logged in for extended period (7 days vs 30 minutes)"
    )
    use_cookies: bool = Field(
        default=False, 
        description="Store tokens as HttpOnly cookies for enhanced security"
    )


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


# ==========================================
# GRADE ENTITIES
# ==========================================

class Grade(SQLModel, table=True):
    """
    📊 **Grade Database Table**
    
    Stores individual course grades for GPA calculation and analytics.
    
    **Table Structure:**
    - Primary key: UUID string (36 chars)
    - Foreign key: Links to user.id
    - Indexed fields: user_id, semester for fast queries
    
    **Business Logic:**
    - GPA points calculated using 10-point scale
    - Supports semesters 1-12 for flexible academic programs
    - Credits range 1-6 per course (typical academic structure)
    
    **Example Record:**
    ```json
    {
        "id": "grade-uuid-123",
        "user_id": "user-uuid-456",
        "course_name": "Data Structures and Algorithms",
        "course_code": "CSE2001",
        "credits": 4,
        "grade": "A",
        "semester": 3,
        "gpa_points": 9.0,
        "created_at": "2025-09-26T18:30:00Z"
    }
    ```
    """
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), 
        primary_key=True, 
        max_length=36,
        description="Unique identifier for the grade record"
    )
    user_id: str = Field(
        foreign_key="user.id", 
        max_length=36,
        description="Reference to the student who earned this grade"
    )
    course_name: str = Field(
        max_length=200,
        description="Full name of the academic course"
    )
    course_code: str = Field(
        max_length=20,
        description="Official course code/identifier"
    )
    credits: int = Field(
        ge=1, le=6,
        description="Credit hours for this course (1-6)"
    )
    grade: str = Field(
        max_length=5,
        description="Letter grade earned (A+, A, B+, B, etc.)"
    )
    semester: int = Field(
        ge=1, le=12,
        description="Academic semester number (1-12)"
    )
    gpa_points: float = Field(
        ge=0.0, le=10.0,
        description="Grade points on 10.0 scale for GPA calculation"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when grade was recorded"
    )


class GradeUpload(SQLModel, table=True):
    """Tracks file uploads for processing"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    user_id: str = Field(foreign_key="user.id", max_length=36)
    filename: str = Field(max_length=255)
    status: str = Field(default="processing", max_length=50)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GradeSchema(SQLModel):
    """Grade data schema"""
    course_code: str
    course_name: str
    credits: int
    grade: str
    grade_points: float
    semester: int


class UploadStatusResponseSchema(SQLModel):
    """Response schema after file upload"""
    upload_id: str
    filename: str
    status: str
    message: str = "File received and is being processed."


class SemesterSummarySchema(SQLModel):
    """Semester summary schema"""
    user_id: str
    semester: int
    subjects_count: int
    total_credits: int
    sgpa: float
    subjects: list[GradeSchema]


class CGPAAnalyticsSchema(SQLModel):
    """
    📈 **CGPA Analytics Response Schema**
    
    Comprehensive academic performance analytics with detailed breakdown.
    
    **Analytics Included:**
    - Overall CGPA calculation
    - Total subjects and credits
    - Semester-wise performance breakdown
    - Academic progress tracking
    
    **Example Response:**
    ```json
    {
        "user_id": "user-uuid-123",
        "total_subjects": 24,
        "total_credits": 96,
        "cgpa": 8.75,
        "semesters_completed": 4,
        "semester_breakdown": [
            {
                "semester": 1,
                "subjects_count": 6,
                "total_credits": 24,
                "sgpa": 8.5,
                "subjects": [...]
            }
        ]
    }
    ```
    """
    user_id: str = Field(description="Student identifier")
    total_subjects: int = Field(description="Total number of subjects completed")
    total_credits: int = Field(description="Total credit hours completed")
    cgpa: float = Field(description="Cumulative Grade Point Average (0.0-10.0)")
    semesters_completed: int = Field(description="Number of semesters with grades")
    semester_breakdown: list[SemesterSummarySchema] = Field(description="Detailed semester-wise performance")


class DeleteResponseSchema(SQLModel):
    """Response schema for delete operations"""
    status: str
    message: str
    deleted_grades: int = 0
    deleted_uploads: int = 0
    semester: Optional[int] = None
    upload_id: Optional[str] = None


# ==========================================
# REFRESH TOKEN ENTITIES
# ==========================================

class RefreshToken(SQLModel, table=True):
    """Refresh token database table for secure session management"""
    
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), 
        primary_key=True, 
        max_length=36
    )
    user_id: str = Field(
        foreign_key="user.id", 
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
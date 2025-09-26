"""
Grade Entity Models  
Database models and Pydantic schemas for grade domain
"""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid


# ==========================================
# DATABASE TABLE MODELS
# ==========================================

class Grade(SQLModel, table=True):
    """Grade database table"""
    __tablename__ = "grades"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    user_id: str = Field(foreign_key="users.id", max_length=36)
    course_name: str = Field(max_length=200)
    course_code: str = Field(max_length=20)
    credits: int = Field(ge=1, le=6)
    grade: str = Field(max_length=5)
    semester: int = Field(ge=1, le=12)
    gpa_points: float = Field(ge=0.0, le=10.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GradeUpload(SQLModel, table=True):
    """Tracks file uploads for processing"""
    __tablename__ = "grade_uploads"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    user_id: str = Field(foreign_key="users.id", max_length=36)
    filename: str = Field(max_length=255)
    status: str = Field(default="processing", max_length=50)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==========================================
# API SCHEMA MODELS
# ==========================================

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
    """CGPA analytics response schema"""
    user_id: str
    total_subjects: int
    total_credits: int
    cgpa: float
    semesters_completed: int
    semester_breakdown: list[SemesterSummarySchema]


class DeleteResponseSchema(SQLModel):
    """Response schema for delete operations"""
    status: str
    message: str
    deleted_grades: int = 0
    deleted_uploads: int = 0
    semester: Optional[int] = None
    upload_id: Optional[str] = None

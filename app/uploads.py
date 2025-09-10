"""
DEPRECATED: File upload endpoints
This functionality has been moved to app/OCR/ocr.py
This file will be removed in the next cleanup
"""
# TODO: Remove this file - functionality moved to OCR module
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import uuid
from typing import List

from .database import get_db_session
from .auth import get_current_user
from .models import User, GradeUpload, UploadStatusResponse

router = APIRouter(prefix="/uploads", tags=["uploads"])
security = HTTPBearer()

# ==========================================
# UPLOAD ENDPOINTS
# ==========================================

@router.post("/grade-sheet", response_model=UploadStatusResponse)
async def upload_grade_sheet(
    file: UploadFile = File(..., description="Grade sheet image (PNG, JPG, PDF)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Upload a grade sheet for OCR processing and AI cleaning
    """
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if file.size and file.size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size: 10MB"
        )
    
    # Create upload record
    upload_record = GradeUpload(
        user_id=current_user.id,
        filename=file.filename or f"upload_{uuid.uuid4().hex[:8]}.{file.content_type.split('/')[-1]}",
        status="uploaded"
    )
    
    db.add(upload_record)
    await db.commit()
    await db.refresh(upload_record)
    
    # TODO: Process file with OCR and AI
    # For now, just return the upload status
    
    return UploadStatusResponse(
        upload_id=upload_record.id,
        filename=upload_record.filename,
        status=upload_record.status,
        message="File uploaded successfully. Processing will begin shortly."
    )


@router.get("/status/{upload_id}")
async def get_upload_status(
    upload_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get the status of an uploaded file
    """
    stmt = select(GradeUpload).where(
        GradeUpload.id == upload_id,
        GradeUpload.user_id == current_user.id
    )
    result = await db.execute(stmt)
    upload = result.scalar_one_or_none()
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    return {
        "upload_id": upload.id,
        "filename": upload.filename,
        "status": upload.status,
        "created_at": upload.created_at
    }


@router.get("/history")
async def get_upload_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> List[dict]:
    """
    Get user's upload history
    """
    stmt = select(GradeUpload).where(GradeUpload.user_id == current_user.id)
    result = await db.execute(stmt)
    uploads = result.scalars().all()
    
    return [
        {
            "upload_id": upload.id,
            "filename": upload.filename,
            "status": upload.status,
            "created_at": upload.created_at
        }
        for upload in uploads
    ]

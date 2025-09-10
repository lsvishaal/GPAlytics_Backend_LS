"""
Grade processing routes for GPAlytics
FastAPI endpoints for result card processing using Gemini Vision
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ..auth import get_current_user
from ..models import User
from ..database import get_db_session, settings
from ..services import store_extracted_grades
from .helper import (
    validate_file_type, 
    validate_file_size, 
    get_allowed_file_types,
    configure_gemini,
    sharpen_image,
    process_result_card,
    validate_extracted_grades
)

logger = logging.getLogger(__name__)

# ==========================================
# REQUEST VALIDATION
# ==========================================

def validate_upload_file(file: UploadFile) -> None:
    """Validate uploaded file using helper functions"""
    
    # Check if content type exists
    if not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content type is missing"
        )
    
    # Check file type
    if not validate_file_type(file.content_type):
        allowed_types = get_allowed_file_types()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{file.content_type}'. Allowed: {', '.join(allowed_types)}"
        )
    
    # Check file size
    if file.size and not validate_file_size(file.size):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size: 10MB"
        )

# ==========================================
# RESULT CARD ROUTER & ENDPOINTS
# ==========================================

router = APIRouter(prefix="/grades", tags=["Grade Processing"])

@router.post("/process-result-card")
async def upload_result_card(
    file: UploadFile = File(..., description="Result card image (PNG, JPG, JPEG)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Process result card image and extract grades using Gemini Vision AI
    
    - **file**: Image file (PNG, JPG, JPEG) containing result card/marksheet
    - **Returns**: Structured grade data with subjects, grades, and CGPA details
    """
    
    # Configure Gemini AI
    configure_gemini(settings.gemini_key_str)
    
    # Validate the uploaded file
    validate_upload_file(file)
    
    # Read file content
    try:
        file_content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}"
        )
    
    # Sharpen image for better AI processing
    try:
        sharpened_image = sharpen_image(file_content)
    except Exception as e:
        logger.warning(f"Image sharpening failed, using original: {str(e)}")
        sharpened_image = file_content
    
    # Process result card using Gemini Vision
    try:
        extracted_data = await process_result_card(sharpened_image)
        
        # Validate extracted data
        if not validate_extracted_grades(extracted_data):
            raise ValueError("Extracted data validation failed")
        
        # Store grades to database
        try:
            storage_result = await store_extracted_grades(
                db=db,
                user_id=current_user.id,
                extracted_data=extracted_data,
                upload_filename=file.filename or "unknown.jpg"
            )
            
            return {
                "success": True,
                "message": "Result card processed and stored successfully",
                "filename": file.filename,
                "user_id": current_user.id,
                "upload_id": storage_result["upload_id"],
                "semester": storage_result["semester"],
                "subjects_stored": storage_result["subjects_stored"],
                "calculated_sgpa": storage_result["calculated_sgpa"],
                "extracted_data": extracted_data
            }
            
        except ValueError as storage_error:
            # Even if storage fails, return the extracted data
            logger.error(f"Storage failed but extraction succeeded: {str(storage_error)}")
            return {
                "success": True,
                "message": "Result card processed successfully, but storage failed",
                "warning": str(storage_error),
                "filename": file.filename,
                "user_id": current_user.id,
                "extracted_data": extracted_data
            }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during result card processing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during result card processing"
        )
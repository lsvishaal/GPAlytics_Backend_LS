"""
Grades Controller
HTTP layer for grade processing endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ..auth import get_current_user
from ..entities import User, UploadStatusResponseSchema, DeleteResponseSchema
from ..core import get_db_session, FileValidationError, OCRProcessingError, DatabaseError
from .service import grades_service
from .ocr import ocr_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/grades", tags=["Grade Processing"])


def validate_upload_file(file: UploadFile) -> None:
    """Validate uploaded file"""
    
    # Check if content type exists
    if not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content type is missing"
        )
    
    # Check file type
    if not ocr_service.validate_file_type(file.content_type):
        allowed_types = ocr_service.get_allowed_file_types()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{file.content_type}'. Allowed: {', '.join(allowed_types)}"
        )
    
    # Check file size
    if file.size and not ocr_service.validate_file_size(file.size):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size: 10MB"
        )


@router.get("/")
async def get_grades(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    **Get All User Grades**
    
    Retrieve all grades for the authenticated user.
    
    **Returns:** List of all grade records
    
    **Possible Errors:**
    - `401`: Authentication required
    - `500`: Database retrieval failed
    """
    try:
        grades = await grades_service.get_user_grades(db, current_user.id)
        return [
            {
                "id": grade.id,
                "course_code": grade.course_code,
                "course_name": grade.course_name,
                "credits": grade.credits,
                "grade": grade.grade,
                "semester": grade.semester,
                "gpa_points": grade.gpa_points
            }
            for grade in grades
        ]
    except DatabaseError as e:
        logger.error(f"Failed to retrieve grades for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve grade data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving grades for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve grades - please try again"
        )


@router.get("/upload-help")
async def get_upload_help():
    """
    **Grade Upload Help & Error Guide**
    
    Comprehensive guide for troubleshooting grade upload issues.
    
    **Returns:** Detailed help information and error explanations
    """
    return {
        "supported_formats": {
            "image_types": ["JPEG", "PNG", "WebP"],
            "max_file_size": "10MB",
            "recommended_resolution": "At least 800x600 pixels"
        },
        "common_errors": {
            "400_file_validation": {
                "description": "Invalid file format or size",
                "solutions": [
                    "Ensure file is JPEG, PNG, or WebP format",
                    "Check file size is under 10MB",
                    "Try converting to JPEG if using other formats"
                ]
            },
            "422_extraction_failed": {
                "description": "AI couldn't extract grade information",
                "solutions": [
                    "Ensure image is clear and well-lit",
                    "Make sure all text is readable",
                    "Remove any shadows or glare",
                    "Try taking photo from directly above the document"
                ]
            },
            "429_rate_limit": {
                "description": "Too many requests to AI service",
                "solutions": [
                    "Wait 2-3 minutes before trying again",
                    "Avoid uploading multiple files simultaneously",
                    "Try during off-peak hours if problem persists"
                ]
            },
            "409_duplicate_grades": {
                "description": "Grades for this semester already exist",
                "solutions": [
                    "Check if you've already uploaded grades for this semester",
                    "Contact support if you need to update existing grades",
                    "Use a different semester if this is a different academic period"
                ]
            },
            "500_processing_error": {
                "description": "Internal processing error",
                "solutions": [
                    "Try again in a few minutes",
                    "Ensure your internet connection is stable",
                    "Contact support if error persists"
                ]
            }
        },
        "tips_for_success": [
            "Take photos in good lighting conditions",
            "Ensure the entire grade sheet is visible in the image",
            "Hold the camera steady to avoid blur",
            "Use the device's camera app rather than screenshots when possible",
            "Make sure grades, course names, and credits are clearly visible"
        ],
        "contact_support": {
            "message": "If you continue to experience issues after following this guide, please contact technical support with the specific error message you received."
        }
    }


@router.get("/delete-help")
async def get_delete_help():
    """
    **Delete Operations Help & Safety Guide**
    
    Comprehensive guide for using the delete endpoints safely and effectively.
    
    **Returns:** Detailed information about delete operations and safety measures
    """
    return {
        "available_operations": {
            "complete_reset": {
                "endpoint": "DELETE /grades/reset",
                "description": "Delete ALL grades and uploads for your account",
                "use_cases": [
                    "Reset account for fresh testing",
                    "Clear all data before re-uploading corrected grades",
                    "Clean slate for demo purposes"
                ],
                "warning": "⚠️ DESTRUCTIVE: Cannot be undone!"
            },
            "semester_deletion": {
                "endpoint": "DELETE /grades/semester/{semester}",
                "description": "Delete grades for a specific semester only",
                "use_cases": [
                    "Re-test specific semester upload",
                    "Correct data for particular academic period",
                    "Selective cleanup during development"
                ],
                "parameters": {
                    "semester": "Integer from 1-12"
                },
                "warning": "⚠️ SELECTIVE: Only affects specified semester"
            },
            "upload_record_deletion": {
                "endpoint": "DELETE /grades/uploads/{upload_id}",
                "description": "Delete specific upload record by ID",
                "use_cases": [
                    "Clean up failed upload records",
                    "Remove test upload entries",
                    "Manage upload history"
                ],
                "parameters": {
                    "upload_id": "UUID of the upload record"
                },
                "note": "Does not affect grade data (grades don't track upload_id currently)"
            }
        },
        "safety_measures": {
            "authentication": "All delete operations require valid JWT authentication",
            "authorization": "Users can only delete their own data",
            "transaction_safety": "All operations use database transactions with rollback on error",
            "audit_logging": "All delete operations are logged with user ID and details",
            "confirmation_required": "No accidental deletions - explicit endpoint calls required"
        },
        "response_format": {
            "structure": {
                "status": "success|no_data|not_found",
                "message": "Human-readable description",
                "deleted_grades": "Number of grade records deleted",
                "deleted_uploads": "Number of upload records deleted",
                "semester": "Semester number (for semester-specific operations)",
                "upload_id": "Upload ID (for upload-specific operations)"
            },
            "status_codes": {
                "200": "Operation successful",
                "401": "Authentication required",
                "404": "No data found to delete",
                "400": "Invalid parameters (e.g., invalid semester)",
                "500": "Server error during operation"
            }
        },
        "testing_workflow": {
            "recommended_sequence": [
                "1. Upload test data using POST /grades/process-result-card",
                "2. Verify data with GET /grades/",
                "3. Test semester deletion with DELETE /grades/semester/{semester}",
                "4. Test complete reset with DELETE /grades/reset",
                "5. Verify deletion with GET /grades/",
                "6. Re-upload to test functionality after reset"
            ],
            "best_practices": [
                "Always check current data before deletion",
                "Use semester deletion for granular testing",
                "Use complete reset for full system tests",
                "Verify results after each delete operation"
            ]
        },
        "integration_notes": {
            "frontend_integration": {
                "confirmation_dialogs": "Implement confirmation dialogs for all delete operations",
                "loading_states": "Show loading indicators during delete operations",
                "error_handling": "Display specific error messages from API responses",
                "success_feedback": "Show clear confirmation of what was deleted"
            },
            "api_usage": {
                "headers": {
                    "Authorization": "Bearer {jwt_token}",
                    "Content-Type": "application/json"
                },
                "error_handling": "Check response.status_code and handle appropriately"
            }
        }
    }
@router.post("/process-result-card", response_model=UploadStatusResponseSchema)
async def process_result_card(
    file: UploadFile = File(..., description="Result card image (JPG, PNG, WEBP, max 10MB)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    **Upload and Process Result Card**
    
    Upload a result card image for AI-powered grade extraction.
    
    **Process:**
    1. Validates file format and size
    2. Processes image with Gemini Vision AI
    3. Extracts grades, credits, and SGPA
    4. Stores data in database
    5. Returns processing status
    
    **Supported Formats:** JPEG, PNG, WebP (max 10MB)
    
    **Returns:** Upload status with processing information
    """
    # Capture user ID early to avoid session issues in error handling
    user_id = current_user.id
    
    try:
        # Validate the uploaded file
        validate_upload_file(file)
        
        logger.info(f"Processing result card upload from user {user_id}: {file.filename}")
        
        # Read file contents
        file_contents = await file.read()
        
        # Sharpen image for better AI processing
        enhanced_image = ocr_service.sharpen_image(file_contents)
        
        # Process with Gemini Vision API
        extracted_data = await ocr_service.process_result_card(enhanced_image)
        
        # Validate extracted data
        if not ocr_service.validate_extracted_grades(extracted_data):
            logger.warning(f"Invalid grade data extracted from {file.filename}")
            
            # Return partial success for debugging
            return UploadStatusResponseSchema(
                upload_id="temp_id",
                filename=file.filename or "unknown",
                status="processing_failed",
                message="Grade extraction failed - please ensure the image is clear and contains grade information"
            )
        
        # Store extracted grades in database
        storage_result = await grades_service.store_extracted_grades(
            db=db,
            user_id=user_id,
            extracted_data=extracted_data,
            upload_filename=file.filename or "unknown"
        )
        
        # Handle different storage outcomes
        if storage_result.get("status") == "all_duplicates":
            duplicate_count = storage_result.get("duplicate_count", 0)
            logger.info(f"All {duplicate_count} grades were duplicates for user {user_id}")
            
            return UploadStatusResponseSchema(
                upload_id=storage_result["upload_id"],
                filename=file.filename or "unknown",
                status="duplicate_detected",
                message=f"All {duplicate_count} subjects already exist for semester {storage_result['semester']}. No new data was added."
            )
        
        logger.info(f"Successfully processed {storage_result['subjects_stored']} subjects for user {user_id}")
        
        return UploadStatusResponseSchema(
            upload_id=storage_result["upload_id"],
            filename=file.filename or "unknown", 
            status="completed",
            message=f"Successfully processed {storage_result['subjects_stored']} subjects. SGPA: {storage_result['calculated_sgpa']}"
        )
        
    except FileValidationError as e:
        logger.error(f"File validation failed for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail=f"File validation error: {str(e)}"
        )
        
    except OCRProcessingError as e:
        logger.error(f"OCR processing failed for user {user_id}: {str(e)}")
        error_message = str(e)
        
        # Provide specific guidance based on error type
        if 'rate limit' in error_message.lower():
            raise HTTPException(
                status_code=429,
                detail="AI service rate limit exceeded. Please wait a few minutes before uploading again."
            )
        elif 'authentication' in error_message.lower():
            raise HTTPException(
                status_code=503,
                detail="AI service configuration error. Please contact support."
            )
        elif 'parsing' in error_message.lower():
            raise HTTPException(
                status_code=422,
                detail="Unable to extract grade information from image. Please ensure the image is clear and contains a valid grade sheet."
            )
        else:
            raise HTTPException(
                status_code=502,
                detail=f"AI processing failed: {error_message}"
            )
        
    except DatabaseError as e:
        logger.error(f"Database error for user {user_id}: {str(e)}")
        error_message = str(e)
        
        # Provide specific guidance for database issues
        if 'duplicate' in error_message.lower():
            raise HTTPException(
                status_code=409,
                detail="Some grades for this semester already exist. Please check your previous uploads or contact support to resolve conflicts."
            )
        elif 'constraint' in error_message.lower():
            raise HTTPException(
                status_code=422,
                detail="Invalid grade data format. Please ensure your result card contains valid academic information."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Database storage failed: {error_message}"
            )
        
    except Exception as e:
        logger.error(f"Unexpected error processing result card for user {user_id}: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")

        # Analyze error for better user feedback
        error_message = str(e)

        if 'timeout' in error_message.lower():
            raise HTTPException(
                status_code=504,
                detail="Processing timeout. Please try again with a smaller or clearer image."
            )
        elif 'memory' in error_message.lower():
            raise HTTPException(
                status_code=413,
                detail="Image too large to process. Please reduce image size and try again."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while processing your grade sheet. Please try again or contact support if the problem persists."
            )


@router.delete("/reset", response_model=DeleteResponseSchema)
async def reset_all_user_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    **Reset All User Grade Data** ⚠️
    
    **DESTRUCTIVE OPERATION**: Delete all grades and uploads for the authenticated user.
    
    This endpoint is designed for testing and development purposes, allowing users to:
    - Clear all uploaded grade data
    - Reset their academic record for fresh testing
    - Remove all upload history
    
    **⚠️ WARNING**: This action cannot be undone!
    
    **Returns:** Summary of deleted records
    
    **Use Cases:**
    - Testing grade upload functionality repeatedly
    - Resetting account for demo purposes
    - Clearing incorrect data after upload mistakes
    
    **Possible Errors:**
    - `401`: Authentication required
    - `404`: No data found to delete
    - `500`: Database operation failed
    """
    # Capture user ID early to avoid session issues
    user_id = current_user.id
    
    try:
        logger.info(f"🗑️ User {user_id} initiated complete data reset")
        
        result = await grades_service.delete_all_user_data(db, user_id)
        
        if result["status"] == "no_data":
            raise HTTPException(
                status_code=404,
                detail="No grade data found to delete"
            )
        
        logger.info(f"✅ Successfully reset all data for user {user_id}: "
                   f"{result['deleted_grades']} grades, {result['deleted_uploads']} uploads")
        
        return DeleteResponseSchema(**result)
        
    except HTTPException:
        raise
    except DatabaseError as e:
        logger.error(f"Database error during reset for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset user data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during reset for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during data reset. Please try again or contact support."
        )


@router.delete("/semester/{semester}", response_model=DeleteResponseSchema)
async def delete_semester_data(
    semester: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    **Delete Semester Data** ⚠️
    
    **SELECTIVE DELETION**: Remove all grades for a specific semester while preserving other semesters.
    
    This endpoint provides granular control for testing and data management:
    - Delete grades for a specific semester only
    - Preserve grades from other semesters
    - Useful for re-testing specific semester uploads
    
    **Parameters:**
    - `semester`: Semester number (1-12) to delete
    
    **⚠️ WARNING**: This action cannot be undone!
    
    **Returns:** Summary of deleted records for the specified semester
    
    **Use Cases:**
    - Re-testing upload for a specific semester
    - Correcting data for a particular academic period
    - Selective cleanup during development
    
    **Possible Errors:**
    - `401`: Authentication required
    - `400`: Invalid semester number
    - `404`: No data found for the specified semester
    - `500`: Database operation failed
    """
    # Validate semester range
    if not (1 <= semester <= 12):
        raise HTTPException(
            status_code=400,
            detail="Semester must be between 1 and 12"
        )
    
    user_id = current_user.id
    
    try:
        logger.info(f"🗑️ User {user_id} initiated deletion of semester {semester} data")
        
        result = await grades_service.delete_semester_data(db, user_id, semester)
        
        if result["status"] == "no_data":
            raise HTTPException(
                status_code=404,
                detail=f"No grade data found for semester {semester}"
            )
        
        logger.info(f"✅ Successfully deleted semester {semester} data for user {user_id}: "
                   f"{result['deleted_grades']} grades")
        
        return DeleteResponseSchema(**result)
        
    except HTTPException:
        raise
    except DatabaseError as e:
        logger.error(f"Database error deleting semester {semester} for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete semester data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting semester {semester} for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during semester deletion. Please try again or contact support."
        )


@router.delete("/uploads/{upload_id}", response_model=DeleteResponseSchema)
async def delete_upload_record(
    upload_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    **Delete Upload Record** ⚠️
    
    **PRECISE DELETION**: Remove a specific upload record from the system.
    
    This endpoint provides the most granular control for upload management:
    - Delete specific upload records by ID
    - Useful for cleaning up failed or test uploads
    - Does not affect grade data (grades don't currently track upload_id)
    
    **Parameters:**
    - `upload_id`: UUID of the upload record to delete
    
    **⚠️ WARNING**: This action cannot be undone!
    
    **Returns:** Summary of deleted upload record
    
    **Use Cases:**
    - Cleaning up failed upload records
    - Removing test upload entries
    - Managing upload history
    
    **Possible Errors:**
    - `401`: Authentication required
    - `400`: Invalid upload ID format
    - `404`: Upload not found or doesn't belong to user
    - `500`: Database operation failed
    """
    user_id = current_user.id
    
    try:
        logger.info(f"🗑️ User {user_id} initiated deletion of upload {upload_id}")
        
        result = await grades_service.delete_upload_data(db, user_id, upload_id)
        
        if result["status"] == "not_found":
            raise HTTPException(
                status_code=404,
                detail="Upload record not found or doesn't belong to you"
            )
        
        logger.info(f"✅ Successfully deleted upload {upload_id} for user {user_id}")
        
        return DeleteResponseSchema(**result)
        
    except HTTPException:
        raise
    except DatabaseError as e:
        logger.error(f"Database error deleting upload {upload_id} for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete upload record: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting upload {upload_id} for user {user_id}: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during upload deletion. Please try again or contact support."
        )

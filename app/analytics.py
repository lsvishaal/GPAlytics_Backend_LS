"""
CGPA and Analytics routes for GPAlytics
Protected endpoints for grade analytics and CGPA calculations
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from typing import Optional

from .auth import get_current_user
from .models import User
from .database import get_db_session
from .services import (
    calculate_user_cgpa,
    get_semester_summary,
    get_user_performance_analytics
)

logger = logging.getLogger(__name__)

# ==========================================
# ANALYTICS ROUTER
# ==========================================

router = APIRouter(prefix="/analytics", tags=["CGPA & Analytics"])

@router.get("/cgpa")
async def get_cgpa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get comprehensive CGPA calculation for the authenticated user
    
    Returns:
    - Overall CGPA
    - Semester-wise SGPA
    - Subject details for each semester
    - Total credits completed
    """
    try:
        cgpa_data = await calculate_user_cgpa(db, current_user.id)
        
        if cgpa_data["total_subjects"] == 0:
            return {
                "success": True,
                "message": "No grades found. Upload your result cards to start tracking your CGPA.",
                "user_info": {
                    "id": current_user.id,
                    "name": current_user.name,
                    "regno": current_user.regno,
                    "batch": current_user.batch
                },
                "cgpa_data": cgpa_data
            }
        
        return {
            "success": True,
            "message": f"CGPA calculated successfully for {cgpa_data['semesters_completed']} semesters",
            "user_info": {
                "id": current_user.id,
                "name": current_user.name,
                "regno": current_user.regno,
                "batch": current_user.batch
            },
            "cgpa_data": cgpa_data
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"CGPA calculation failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate CGPA"
        )

@router.get("/semester")
@router.get("/semester/{semester_number}")
async def get_semester_grades(
    semester_number: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get semester academic details - conditional based on parameter
    
    **Two Usage Modes:**
    - `/analytics/semester` - Returns ALL semesters + overall CGPA
    - `/analytics/semester/{number}` - Returns specific semester + motivational message
    
    Args:
    - semester_number (optional): Semester number (1-12)
    
    Returns:
    - If semester_number provided: Specific semester data with motivational context
    - If no semester_number: All semesters overview with CGPA
    """
    # Validate semester parameter if provided
    if semester_number is not None and (semester_number < 1 or semester_number > 12):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Semester number must be between 1 and 12"
        )
    try:
        # Case 1: Get overall CGPA data (needed for both cases)
        cgpa_data = await calculate_user_cgpa(db, current_user.id)
        
        # Handle case: No academic data found
        if cgpa_data["total_subjects"] == 0:
            if semester_number is not None:
                return {
                    "success": True,
                    "message": f"No grades found for semester {semester_number}. Upload your result cards first! 📚",
                    "user_info": {
                        "id": current_user.id,
                        "name": current_user.name,
                        "regno": current_user.regno,
                        "batch": current_user.batch
                    },
                    "semester_data": None,
                    "greet_msg": "🌟 Ready to begin your academic journey? Upload your first result card! 🚀"
                }
            else:
                return {
                    "success": True,
                    "message": "No academic records found. Upload your result cards to start tracking! 📈",
                    "user_info": {
                        "id": current_user.id,
                        "name": current_user.name,
                        "regno": current_user.regno,
                        "batch": current_user.batch
                    },
                    "all_semesters": [],
                    "CGPA": 0.0,
                    "total_credits": 0,
                    "semesters_completed": 0
                }
        
        # Case A: Specific semester requested
        if semester_number is not None:
            semester_data = await get_semester_summary(db, current_user.id, semester_number)
            
            if not semester_data:
                return {
                    "success": True,
                    "message": f"No grades found for semester {semester_number}",
                    "user_info": {
                        "id": current_user.id,
                        "name": current_user.name,
                        "regno": current_user.regno
                    },
                    "semester": semester_number,
                    "data": None,
                    "greet_msg": f"🎯 Semester {semester_number} data not found. Upload the result card for this semester! 📚"
                }
            
            # Generate motivational message based on performance
            sgpa = semester_data.get("sgpa", 0.0)
            
            # Simple motivational message generation
            if sgpa >= 9.0:
                greet_msg = f"🌟 Outstanding performance in semester {semester_number}! You're setting the gold standard! 👑"
            elif sgpa >= 8.0:
                greet_msg = f"🎯 Excellent work in semester {semester_number}! Keep this momentum going! 🚀"
            elif sgpa >= 7.0:
                greet_msg = f"📚 Good progress in semester {semester_number}! You're building a solid foundation! 💪"
            else:
                greet_msg = f"🌱 Every step counts in semester {semester_number}! Keep pushing forward! 💪"
            
            return {
                "success": True,
                "message": f"Semester {semester_number} data retrieved successfully",
                "user_info": {
                    "id": current_user.id,
                    "name": current_user.name,
                    "regno": current_user.regno
                },
                "data": {
                    "semester": semester_number,
                    "grades": [
                        {
                            "course_name": subject["course_name"],
                            "course_code": subject["course_code"], 
                            "course_credit": subject["credits"],
                            "grade": subject["grade"]
                        }
                        for subject in semester_data["subjects"]
                    ],
                    "gpa": semester_data["sgpa"],
                    "credits_sem": semester_data["total_credits"],
                    "subjects_count": semester_data["subjects_count"]
                },
                "greet_msg": greet_msg
            }
        
        # Case B: All semesters requested (no semester_number provided)
        else:
            semester_results = []
            
            for sem_data in cgpa_data["semester_wise"]:
                semester_results.append({
                    "semester": sem_data["semester"],
                    "grades": [
                        {
                            "course_name": subject["course_name"],
                            "course_code": subject["course_code"],
                            "course_credit": subject["credits"], 
                            "grade": subject["grade"]
                        }
                        for subject in sem_data["subjects"]
                    ],
                    "gpa": sem_data["sgpa"],
                    "credits_sem": sem_data["total_credits"]
                })
            
            return {
                "success": True,
                "message": f"Academic overview retrieved for {cgpa_data['semesters_completed']} semesters",
                "user_info": {
                    "id": current_user.id,
                    "name": current_user.name,
                    "regno": current_user.regno,
                    "batch": current_user.batch
                },
                "all_result": semester_results,
                "CGPA": cgpa_data["cgpa"],
                "total_credits": cgpa_data["total_credits"],
                "semesters_completed": cgpa_data["semesters_completed"]
            }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        error_context = f"semester {semester_number}" if semester_number else "all semesters"
        logger.error(f"Semester data retrieval failed for user {current_user.id}, {error_context}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve semester data"
        )

@router.get("/performance")
async def get_performance_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get comprehensive performance analytics for the authenticated user
    
    Returns:
    - CGPA trends
    - Grade distribution
    - Performance metrics
    - Semester comparisons
    """
    try:
        analytics_data = await get_user_performance_analytics(db, current_user.id)
        
        return {
            "success": True,
            "message": "Performance analytics calculated successfully",
            "user_info": {
                "id": current_user.id,
                "name": current_user.name,
                "regno": current_user.regno,
                "batch": current_user.batch
            },
            "analytics": analytics_data
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Performance analytics failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate performance analytics"
        )

@router.get("/transcript")
async def get_transcript(
    format: Optional[str] = Query(default="detailed", description="Format: 'detailed' or 'summary'"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get academic transcript with all grades and CGPA
    
    Args:
    - format: 'detailed' (all subjects) or 'summary' (semester-wise only)
    
    Returns:
    - Complete academic record
    - CGPA calculation
    - Semester-wise breakdown
    """
    if format not in ["detailed", "summary"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format must be 'detailed' or 'summary'"
        )
    
    try:
        cgpa_data = await calculate_user_cgpa(db, current_user.id)
        
        if cgpa_data["total_subjects"] == 0:
            return {
                "success": True,
                "message": "No academic records found",
                "user_info": {
                    "id": current_user.id,
                    "name": current_user.name,
                    "regno": current_user.regno,
                    "batch": current_user.batch
                },
                "transcript": {
                    "cgpa": 0.0,
                    "total_credits": 0,
                    "semesters": []
                }
            }
        
        # Prepare transcript based on format
        if format == "summary":
            # Remove detailed subject lists for summary format
            semester_wise = []
            for sem in cgpa_data["semester_wise"]:
                semester_wise.append({
                    "semester": sem["semester"],
                    "subjects_count": sem["subjects_count"],
                    "total_credits": sem["total_credits"],
                    "sgpa": sem["sgpa"]
                })
        else:
            semester_wise = cgpa_data["semester_wise"]
        
        return {
            "success": True,
            "message": f"Academic transcript generated ({format} format)",
            "user_info": {
                "id": current_user.id,
                "name": current_user.name,
                "regno": current_user.regno,
                "batch": current_user.batch
            },
            "transcript": {
                "cgpa": cgpa_data["cgpa"],
                "total_subjects": cgpa_data["total_subjects"],
                "total_credits": cgpa_data["total_credits"],
                "semesters_completed": cgpa_data["semesters_completed"],
                "semester_wise": semester_wise
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Transcript generation failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate transcript"
        )

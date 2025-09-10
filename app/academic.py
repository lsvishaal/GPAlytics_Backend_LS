"""
Academic records and semester analytics endpoints for GPAlytics
Enhanced unified endpoint for semester data with motivational context
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
    get_semester_summary
)

logger = logging.getLogger(__name__)

# ==========================================
# MOTIVATIONAL MESSAGES
# ==========================================

def get_performance_message(sgpa: float, cgpa: float, semester: int) -> str:
    """
    Generate motivational messages based on academic performance
    Returns contextual encouragement based on grades
    """
    try:
        if sgpa >= 9.5:
            messages = [
                "🌟 Absolutely phenomenal! You're setting the gold standard! 👑",
                "🚀 Outstanding performance! You're in the league of legends! ⭐",
                "🏆 Exceptional work! You're crushing every expectation! 💯",
                "✨ You're not just acing it—you've mastered perfection! 🌟👑"
            ]
        elif sgpa >= 8.5:
            messages = [
                "🎯 Excellent work! You're consistently performing at a high level! 📈",
                "💪 Great job! Your dedication is clearly paying off! 🌟",
                "🔥 Impressive performance! Keep this momentum going! 🚀",
                "👏 Well done! You're on the path to greatness! ⭐"
            ]
        elif sgpa >= 7.5:
            messages = [
                "📚 Good progress! You're building a solid foundation! 💪",
                "🎊 Nice work! Every step forward counts! 📈",
                "🌱 Steady growth! Your efforts are making a difference! 🌟",
                "👍 Keep it up! You're on the right track! 🎯"
            ]
        elif sgpa >= 6.5:
            messages = [
                "🌈 Every challenge is a chance to grow stronger! 💪",
                "🚀 You've got this! Focus on your strengths and build from there! 📈",
                "🌟 Progress isn't always linear - you're learning and improving! 📚",
                "💡 Each semester is a new opportunity to shine! ✨"
            ]
        else:
            messages = [
                "🌅 New beginnings start with believing in yourself! 💪",
                "🌱 Growth happens step by step - you're on your journey! 🚀",
                "💫 Your potential is unlimited - keep pushing forward! 🌟",
                "🎯 Focus on progress, not perfection - you've got this! 📈"
            ]
        
        # Add semester-specific context
        import random
        base_message = random.choice(messages)
        
        if semester <= 2:
            context = " Great start to your academic journey! 🎓"
        elif semester <= 4:
            context = " You're building momentum nicely! 📚"
        elif semester <= 6:
            context = " Halfway through - keep the energy up! ⚡"
        else:
            context = " Final stretch - finish strong! 🏁"
            
        return base_message + context
        
    except Exception as e:
        logger.error(f"Error generating performance message: {str(e)}")
        return "🌟 Keep pushing forward - every effort counts! 💪"

# ==========================================
# ACADEMIC ROUTER
# ==========================================

router = APIRouter(prefix="/academic", tags=["Academic Records"])

@router.get("/semesters")
async def get_semester_details(
    sem: Optional[int] = Query(None, description="Semester number (1-12). If not provided, returns all semesters"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get semester-wise academic details with motivational context
    
    - **No sem parameter**: Returns all semesters + overall CGPA
    - **With sem parameter**: Returns specific semester + motivational message
    
    Returns comprehensive academic overview or focused semester insights
    """
    try:
        # Validate semester parameter if provided
        if sem is not None and (sem < 1 or sem > 12):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Semester must be between 1 and 12"
            )
        
        # Get overall CGPA data first (always needed)
        try:
            cgpa_data = await calculate_user_cgpa(db, current_user.id)
        except ValueError as e:
            logger.error(f"CGPA calculation failed for user {current_user.id}: {str(e)}")
            # Graceful fallback for CGPA calculation errors
            cgpa_data = {
                "user_id": current_user.id,
                "total_subjects": 0,
                "total_credits": 0,
                "cgpa": 0.0,
                "semesters_completed": 0,
                "semester_wise": []
            }
        
        # Handle case: No academic data found
        if cgpa_data["total_subjects"] == 0:
            if sem is not None:
                return {
                    "success": True,
                    "message": f"No grades found for semester {sem}. Start by uploading your result cards! 📚",
                    "user_info": {
                        "id": current_user.id,
                        "name": current_user.name,
                        "regno": current_user.regno,
                        "batch": current_user.batch
                    },
                    "semester_details": None,
                    "greet_msg": "🌟 Ready to begin your academic journey? Upload your first result card! 🚀"
                }
            else:
                return {
                    "success": True,
                    "message": "No academic records found. Upload your result cards to start tracking your progress! 📈",
                    "user_info": {
                        "id": current_user.id,
                        "name": current_user.name,
                        "regno": current_user.regno,
                        "batch": current_user.batch
                    },
                    "all_semesters": [],
                    "cgpa": 0.0,
                    "total_credits": 0,
                    "semesters_completed": 0
                }
        
        # Case 1: Specific semester requested
        if sem is not None:
            try:
                semester_data = await get_semester_summary(db, current_user.id, sem)
                
                if not semester_data:
                    return {
                        "success": True,
                        "message": f"No grades found for semester {sem}",
                        "user_info": {
                            "id": current_user.id,
                            "name": current_user.name,
                            "regno": current_user.regno,
                            "batch": current_user.batch
                        },
                        "semester_details": None,
                        "greet_msg": f"🎯 Semester {sem} data not found. Try uploading the result card for this semester! 📚"
                    }
                
                # Generate motivational message
                sgpa = semester_data.get("sgpa", 0.0)
                overall_cgpa = cgpa_data.get("cgpa", 0.0)
                greet_msg = get_performance_message(sgpa, overall_cgpa, sem)
                
                return {
                    "success": True,
                    "message": f"Semester {sem} details retrieved successfully",
                    "user_info": {
                        "id": current_user.id,
                        "name": current_user.name,
                        "regno": current_user.regno,
                        "batch": current_user.batch
                    },
                    "semester_details": {
                        "semester": sem,
                        "grades": semester_data["subjects"],
                        "gpa": sgpa,
                        "credits_sem": semester_data["total_credits"],
                        "subjects_count": semester_data["subjects_count"]
                    },
                    "greet_msg": greet_msg
                }
                
            except ValueError as e:
                logger.error(f"Semester summary failed for user {current_user.id}, semester {sem}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to retrieve semester {sem} data"
                )
        
        # Case 2: All semesters requested  
        else:
            try:
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
                
            except Exception as e:
                logger.error(f"All semesters data processing failed for user {current_user.id}: {str(e)}")
                # Graceful fallback with basic data
                return {
                    "success": True,
                    "message": "Academic data retrieved with limited details due to processing issues",
                    "user_info": {
                        "id": current_user.id,
                        "name": current_user.name,
                        "regno": current_user.regno,
                        "batch": current_user.batch
                    },
                    "all_result": [],
                    "CGPA": cgpa_data.get("cgpa", 0.0),
                    "total_credits": cgpa_data.get("total_credits", 0),
                    "semesters_completed": cgpa_data.get("semesters_completed", 0),
                    "warning": "Some data processing issues occurred. Please try again later."
                }
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, etc.)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in semester details endpoint for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving academic data"
        )

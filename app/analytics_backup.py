"""
Academic Analytics API
CGPA calculations and semester data retrieval
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from typing import Optional

from .auth import get_current_user
from .models import User
from .database import get_db_session
from .services import calculate_user_cgpa, get_semester_summary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Academic Analytics"])

@router.get("/cgpa", summary="Get Overall CGPA")
async def get_overall_cgpa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    **Get Overall CGPA and Academic Summary**
    
    Returns:
    - Overall CGPA calculation
    - Total credits completed  
    - Semester-wise breakdown
    - Subject count and distribution
    
    **Response Example:**
    ```json
    {
        "success": true,
        "cgpa_data": {
            "cgpa": 8.5,
            "total_credits": 120,
            "semesters_completed": 6
        }
    }
    ```
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
            "message": "CGPA retrieved successfully",
            "user_info": {
                "id": current_user.id,
                "name": current_user.name,
                "regno": current_user.regno,
                "batch": current_user.batch
            },
            "cgpa_data": cgpa_data
        }
        
    except Exception as e:
        logger.error(f"CGPA calculation failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate CGPA"
        )

@router.get("/semesters", summary="Get All Semesters")
@router.get("/semesters/{semester_number}", summary="Get Specific Semester")
async def get_semester_data(
    semester_number: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    **Get Semester Academic Data**
    
    **Without semester_number:** Returns all semesters with grades
    **With semester_number:** Returns specific semester (1-12)
    
    **Path Parameters:**
    - `semester_number` (optional): Semester number (1-12)
    
    **Response Examples:**
    
    *All Semesters:*
    ```json
    {
        "success": true,
        "all_semesters": [
            {
                "semester": 1,
                "sgpa": 8.2,
                "total_credits": 20
            }
        ],
        "overall_cgpa": 8.5
    }
    ```
    
    *Specific Semester:*
    ```json
    {
        "success": true,
        "semester": 1,
        "data": {
            "sgpa": 8.2,
            "subjects": [...]
        }
    }
    ```
    """
    try:
        if semester_number:
            # Get specific semester
            semester_data = await get_semester_summary(db, current_user.id, semester_number)
            
            if not semester_data:
                return {
                    "success": True,
                    "message": f"No grades found for semester {semester_number}. Upload your result cards to track progress.",
                    "user_info": {
                        "id": current_user.id,
                        "name": current_user.name,
                        "regno": current_user.regno,
                        "batch": current_user.batch
                    },
                    "semester": semester_number,
                    "data": None
                }
            
            return {
                "success": True,
                "message": f"Semester {semester_number} grades retrieved successfully",
                "user_info": {
                    "id": current_user.id,
                    "name": current_user.name,
                    "regno": current_user.regno,
                    "batch": current_user.batch
                },
                "semester": semester_number,
                "data": semester_data
            }
        else:
            # Get all semesters
            cgpa_data = await calculate_user_cgpa(db, current_user.id)
            
            if cgpa_data["total_subjects"] == 0:
                return {
                    "success": True,
                    "message": "No academic records found. Upload your result cards to start tracking your progress.",
                    "user_info": {
                        "id": current_user.id,
                        "name": current_user.name,
                        "regno": current_user.regno,
                        "batch": current_user.batch
                    },
                    "all_semesters": [],
                    "total_semesters": 0
                }
            
            return {
                "success": True,
                "message": f"All semester data retrieved successfully",
                "user_info": {
                    "id": current_user.id,
                    "name": current_user.name,
                    "regno": current_user.regno,
                    "batch": current_user.batch
                },
                "all_semesters": cgpa_data["semester_breakdown"],
                "total_semesters": cgpa_data["semesters_completed"],
                "overall_cgpa": cgpa_data["cgpa"]
            }
        
    except Exception as e:
        logger.error(f"Semester analytics failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve semester data"
        )

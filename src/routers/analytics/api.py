"""Analytics API (feature-based)
Moved from app/features/analytics/api.py with adjusted imports
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from typing import Optional

from ..auth import get_current_user
from ...shared.entities import User
from ...shared.database import get_db_session
from ...shared.exceptions import DatabaseError
from .service import analytics_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Academic Analytics"])


@router.get("/cgpa", summary="Get Overall CGPA")
async def get_overall_cgpa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        cgpa_data = await analytics_service.calculate_user_cgpa(db, current_user.id)

        if cgpa_data["total_subjects"] == 0:
            return {
                "success": True,
                "message": "No grades found. Upload your result cards to start tracking your CGPA.",
                "user_info": {
                    "id": current_user.id,
                    "name": current_user.name,
                    "regno": current_user.regno,
                    "batch": current_user.batch,
                },
                "cgpa_data": cgpa_data,
            }

        return {
            "success": True,
            "message": "CGPA retrieved successfully",
            "user_info": {
                "id": current_user.id,
                "name": current_user.name,
                "regno": current_user.regno,
                "batch": current_user.batch,
            },
            "cgpa_data": cgpa_data,
        }

    except DatabaseError:
        logger.exception("CGPA calculation failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to calculate CGPA")


@router.get("/semesters", summary="Get All Semesters")
@router.get("/semesters/{semester_number}", summary="Get Specific Semester")
async def get_semester_data(
    semester_number: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        if semester_number:
            semester_data = await analytics_service.get_semester_summary(db, current_user.id, semester_number)

            if not semester_data:
                return {
                    "success": True,
                    "message": f"No grades found for semester {semester_number}. Upload your result cards to track progress.",
                    "user_info": {
                        "id": current_user.id,
                        "name": current_user.name,
                        "regno": current_user.regno,
                        "batch": current_user.batch,
                    },
                    "semester": semester_number,
                    "data": None,
                }

            return {
                "success": True,
                "message": f"Semester {semester_number} grades retrieved successfully",
                "user_info": {
                    "id": current_user.id,
                    "name": current_user.name,
                    "regno": current_user.regno,
                    "batch": current_user.batch,
                },
                "semester": semester_number,
                "data": semester_data,
            }
        else:
            cgpa_data = await analytics_service.calculate_user_cgpa(db, current_user.id)

            if cgpa_data["total_subjects"] == 0:
                return {
                    "success": True,
                    "message": "No academic records found. Upload your result cards to start tracking your progress.",
                    "user_info": {
                        "id": current_user.id,
                        "name": current_user.name,
                        "regno": current_user.regno,
                        "batch": current_user.batch,
                    },
                    "all_semesters": [],
                    "total_semesters": 0,
                }

            return {
                "success": True,
                "message": "All semester data retrieved successfully",
                "user_info": {
                    "id": current_user.id,
                    "name": current_user.name,
                    "regno": current_user.regno,
                    "batch": current_user.batch,
                },
                "all_semesters": cgpa_data["semester_breakdown"],
                "total_semesters": cgpa_data["semesters_completed"],
                "overall_cgpa": cgpa_data["cgpa"],
            }

    except DatabaseError:
        logger.exception("Semester analytics failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve semester data")


@router.get("/")
async def analytics_root(
    semester: Optional[int] = Query(default=None, ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Compatibility endpoint: mirrors older analytics root behavior.

    - Without `semester`: returns a simplified payload with `semesters` list and `overall_cgpa`.
    - With `semester`: returns data for that semester.
    """
    try:
        if semester is not None:
            data = await analytics_service.get_semester_summary(db, current_user.id, semester)
            return {
                "semester": semester,
                "data": data,
            }

        cgpa_data = await analytics_service.calculate_user_cgpa(db, current_user.id)
        return {
            "semesters": cgpa_data.get("semester_breakdown", []),
            "overall_cgpa": cgpa_data.get("cgpa", 0.0),
        }
    except DatabaseError:
        logger.exception("Analytics root failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve analytics data")

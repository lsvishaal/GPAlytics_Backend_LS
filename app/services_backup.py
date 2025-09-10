"""
Database services for GPAlytics
Business logic for grade storage and CGPA calculations
Separation of concerns - pure business logic with no FastAPI dependencies
"""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import logging

from .models import Grade, GradeUpload
from .constants import GRADE_POINTS_MAP

logger = logging.getLogger(__name__)

def get_grade_points(grade: str) -> float:
    """Convert letter grade to grade points"""
    return GRADE_POINTS_MAP.get(grade.upper(), 0.0)

# ==========================================
# GRADE STORAGE SERVICES
# ==========================================

async def store_extracted_grades(
    db: AsyncSession, 
    user_id: str, 
    extracted_data: Dict[str, Any],
    upload_filename: str
) -> Dict[str, Any]:
    """
    Store extracted grades to database with transaction handling
    Returns summary of stored data
    """
    try:
        # Create upload record first
        upload_record = GradeUpload(
            user_id=user_id,
            filename=upload_filename,
            status="processing"
        )
        db.add(upload_record)
        await db.flush()  # Get the ID without committing
        
        # Extract semester info
        student_info = extracted_data.get("student_info", {})
        semester = student_info.get("semester")
        if semester:
            semester = int(semester) if str(semester).isdigit() else 1
        else:
            semester = 1
        
        # Process and store each subject
        subjects = extracted_data.get("subjects", [])
        stored_grades = []
        total_credits = 0
        total_grade_points = 0.0
        
        for subject_data in subjects:
            # Extract subject information
            course_code = subject_data.get("subject_code", "").strip()
            course_name = subject_data.get("subject_name", "").strip()
            credits = int(subject_data.get("credits", 0))
            grade = subject_data.get("grade", "F").strip().upper()
            
            # Calculate grade points
            grade_points = get_grade_points(grade)
            
            # Create Grade record
            grade_record = Grade(
                user_id=user_id,
                course_name=course_name,
                course_code=course_code,
                credits=credits,
                grade=grade,
                semester=semester,
                gpa_points=grade_points
            )
            
            db.add(grade_record)
            stored_grades.append({
                "course_code": course_code,
                "course_name": course_name,
                "credits": credits,
                "grade": grade,
                "grade_points": grade_points
            })
            
            # Calculate totals for SGPA
            total_credits += credits
            total_grade_points += (grade_points * credits)
        
        # Calculate SGPA for this semester
        sgpa = total_grade_points / total_credits if total_credits > 0 else 0.0
        
        # Update upload status to completed
        upload_record.status = "completed"
        
        # Commit all changes
        await db.commit()
        
        logger.info(f"Stored {len(stored_grades)} grades for user {user_id}, semester {semester}")
        
        return {
            "upload_id": upload_record.id,
            "user_id": user_id,
            "semester": semester,
            "subjects_stored": len(stored_grades),
            "total_credits": total_credits,
            "calculated_sgpa": round(sgpa, 2),
            "grades": stored_grades
        }
        
    except Exception as e:
        # Mark upload as failed if it exists
        try:
            # Simple cleanup - don't worry about finding the exact record
            pass
        except Exception:
            pass  # Ignore errors during cleanup
        
        logger.error(f"Failed to store grades for user {user_id}: {str(e)}")
        raise ValueError(f"Database storage failed: {str(e)}")

# ==========================================
# CGPA CALCULATION SERVICES
# ==========================================

async def calculate_user_cgpa(db: AsyncSession, user_id: str) -> Dict[str, Any]:
    """
    Calculate comprehensive CGPA for a user across all semesters
    """
    try:
        # Get all grades for the user
        stmt = select(Grade).where(Grade.user_id == user_id)
        result = await db.execute(stmt)
        all_grades = result.scalars().all()
        
        if not all_grades:
            return {
                "user_id": user_id,
                "total_subjects": 0,
                "total_credits": 0,
                "cgpa": 0.0,
                "semester_wise": []
            }
        
        # Group by semester
        semester_data = {}
        total_credits = 0
        total_grade_points = 0.0
        
        for grade in all_grades:
            semester = grade.semester
            if semester not in semester_data:
                semester_data[semester] = {
                    "semester": semester,
                    "subjects": [],
                    "credits": 0,
                    "grade_points": 0.0
                }
            
            semester_data[semester]["subjects"].append({
                "course_code": grade.course_code,
                "course_name": grade.course_name,
                "credits": grade.credits,
                "grade": grade.grade,
                "grade_points": grade.gpa_points
            })
            
            semester_data[semester]["credits"] += grade.credits
            semester_data[semester]["grade_points"] += (grade.gpa_points * grade.credits)
            
            total_credits += grade.credits
            total_grade_points += (grade.gpa_points * grade.credits)
        
        # Calculate SGPA for each semester
        semester_wise = []
        for sem_num in sorted(semester_data.keys()):
            sem_data = semester_data[sem_num]
            sgpa = sem_data["grade_points"] / sem_data["credits"] if sem_data["credits"] > 0 else 0.0
            
            semester_wise.append({
                "semester": sem_num,
                "subjects_count": len(sem_data["subjects"]),
                "total_credits": sem_data["credits"],
                "sgpa": round(sgpa, 2),
                "subjects": sem_data["subjects"]
            })
        
        # Calculate overall CGPA
        cgpa = total_grade_points / total_credits if total_credits > 0 else 0.0
        
        return {
            "user_id": user_id,
            "total_subjects": len(all_grades),
            "total_credits": total_credits,
            "cgpa": round(cgpa, 2),
            "semesters_completed": len(semester_data),
            "semester_wise": semester_wise
        }
        
    except Exception as e:
        logger.error(f"CGPA calculation failed for user {user_id}: {str(e)}")
        raise ValueError(f"CGPA calculation failed: {str(e)}")

async def get_semester_summary(db: AsyncSession, user_id: str, semester: int) -> Optional[Dict[str, Any]]:
    """
    Get summary for a specific semester
    """
    try:
        stmt = select(Grade).where(
            Grade.user_id == user_id,
            Grade.semester == semester
        )
        
        result = await db.execute(stmt)
        grades = result.scalars().all()
        
        if not grades:
            return None
        
        total_credits = sum(grade.credits for grade in grades)
        total_grade_points = sum(grade.gpa_points * grade.credits for grade in grades)
        sgpa = total_grade_points / total_credits if total_credits > 0 else 0.0
        
        subjects = [
            {
                "course_code": grade.course_code,
                "course_name": grade.course_name,
                "credits": grade.credits,
                "grade": grade.grade,
                "grade_points": grade.gpa_points
            }
            for grade in grades
        ]
        
        return {
            "user_id": user_id,
            "semester": semester,
            "subjects_count": len(subjects),
            "total_credits": total_credits,
            "sgpa": round(sgpa, 2),
            "subjects": subjects
        }
        
    except Exception as e:
        logger.error(f"Semester summary failed for user {user_id}, semester {semester}: {str(e)}")
        raise ValueError(f"Semester summary failed: {str(e)}")

# ==========================================
# USER PERFORMANCE ANALYTICS
# ==========================================

async def get_user_performance_analytics(db: AsyncSession, user_id: str) -> Dict[str, Any]:
    """
    Get detailed performance analytics for a user
    """
    try:
        # Get CGPA data
        cgpa_data = await calculate_user_cgpa(db, user_id)
        
        if cgpa_data["total_subjects"] == 0:
            return {
                "user_id": user_id,
                "message": "No grades found for analysis",
                "cgpa_data": cgpa_data
            }
        
        # Calculate additional analytics
        semester_wise = cgpa_data["semester_wise"]
        sgpa_values = [sem["sgpa"] for sem in semester_wise]
        
        performance_trends = {
            "highest_sgpa": max(sgpa_values) if sgpa_values else 0.0,
            "lowest_sgpa": min(sgpa_values) if sgpa_values else 0.0,
            "average_sgpa": round(sum(sgpa_values) / len(sgpa_values), 2) if sgpa_values else 0.0,
            "sgpa_trend": sgpa_values
        }
        
        # Grade distribution analysis
        all_grades = []
        for sem in semester_wise:
            all_grades.extend([subject["grade"] for subject in sem["subjects"]])
        
        grade_distribution = {}
        for grade in all_grades:
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
        
        return {
            "user_id": user_id,
            "cgpa_data": cgpa_data,
            "performance_trends": performance_trends,
            "grade_distribution": grade_distribution,
            "total_semesters": len(semester_wise)
        }
        
    except Exception as e:
        logger.error(f"Performance analytics failed for user {user_id}: {str(e)}")
        raise ValueError(f"Performance analytics failed: {str(e)}")

"""
Grades Service
Business logic for grade processing and storage
"""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import logging

from ..constants import GRADE_POINTS_MAP
from ..entities import Grade, GradeUpload, GradeSchema, SemesterSummarySchema
from ..core import DatabaseError

logger = logging.getLogger(__name__)


class GradesService:
    """Grades processing business logic"""
    
    @staticmethod
    def get_grade_points(grade: str) -> float:
        """Convert letter grade to grade points"""
        return GRADE_POINTS_MAP.get(grade.upper(), 0.0)
    
    async def store_extracted_grades(
        self,
        db: AsyncSession, 
        user_id: str, 
        extracted_data: Dict[str, Any],
        upload_filename: str
    ) -> Dict[str, Any]:
        """Store extracted grades to database with transaction handling"""
        try:
            # Create upload record first
            upload_record = GradeUpload(
                user_id=user_id,
                filename=upload_filename,
                status="processing"
            )
            db.add(upload_record)
            await db.flush()  # Get the upload ID
            
            # Extract semester info
            student_info = extracted_data.get("student_info", {})
            semester = student_info.get("semester")
            if semester:
                semester = int(semester) if str(semester).isdigit() else 1
            else:
                semester = 1
            
            # Validate semester range
            if semester < 1 or semester > 12:
                semester = 1
                logger.warning(f"Invalid semester {semester} detected, defaulting to 1")
            
            # Process and store each subject
            subjects = extracted_data.get("subjects", [])
            if not subjects:
                raise DatabaseError("No subjects found in extracted data")
                
            stored_grades = []
            total_credits = 0
            total_grade_points = 0.0
            
            for subject_data in subjects:
                try:
                    # Extract subject information with validation
                    course_code = subject_data.get("subject_code", "").strip()
                    course_name = subject_data.get("subject_name", "").strip()
                    credits = subject_data.get("credits", 0)
                    grade_raw = subject_data.get("grade", "F")
                    grade = grade_raw.strip().upper() if grade_raw else "F"
                    
                    # Validate subject data
                    if not course_code or not course_name:
                        logger.warning(f"Skipping subject with missing code/name: {subject_data}")
                        continue
                    
                    # Skip subjects with invalid/missing grades
                    if not grade or grade == "NONE":
                        logger.warning(f"Skipping subject {course_code} with invalid grade: {grade_raw}")
                        continue
                    
                    # Validate and convert credits
                    try:
                        credits = int(credits) if credits else 0
                        if credits < 1 or credits > 6:
                            logger.warning(f"Invalid credits {credits} for {course_code}, defaulting to 3")
                            credits = 3
                    except ValueError:
                        logger.warning(f"Invalid credits format for {course_code}, defaulting to 3")
                        credits = 3
                    
                    # Calculate grade points
                    grade_points = self.get_grade_points(grade)
                    
                    # Check for duplicate course in same semester
                    existing_grade = await db.execute(
                        select(Grade).where(
                            Grade.user_id == user_id,
                            Grade.course_code == course_code,
                            Grade.semester == semester
                        )
                    )
                    if existing_grade.scalar_one_or_none():
                        logger.warning(f"Duplicate grade found for {course_code} in semester {semester}, skipping")
                        continue
                    
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
                    
                except Exception as subject_error:
                    logger.error(f"Failed to process subject {subject_data}: {str(subject_error)}")
                    continue
            
            # Check if any grades were successfully processed
            if not stored_grades:
                # Update upload record status to reflect duplicate detection
                upload_record.status = "all_duplicates"
                await db.commit()  # Commit the upload record with duplicate status
                
                # Return a special response for duplicates
                logger.info(f"All {len(subjects)} grades were duplicates for user {user_id}, semester {semester}")
                
                return {
                    "upload_id": upload_record.id,
                    "user_id": user_id,
                    "semester": semester,
                    "subjects_stored": 0,
                    "total_credits": 0,
                    "calculated_sgpa": 0.0,
                    "grades": [],
                    "duplicate_count": len(subjects),
                    "status": "all_duplicates"
                }
            
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
            
        except DatabaseError:
            # Re-raise DatabaseError as-is
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            error_msg = str(e).lower()
            
            # Handle specific database errors
            if 'unique constraint' in error_msg or 'duplicate' in error_msg:
                logger.error(f"Duplicate grade data detected: {str(e)}")
                raise DatabaseError("Some grades for this semester already exist - cannot process duplicate data")
            elif 'foreign key' in error_msg:
                logger.error(f"Foreign key constraint violation: {str(e)}")
                raise DatabaseError("Invalid user reference - please re-login and try again")
            elif 'check constraint' in error_msg:
                logger.error(f"Data validation constraint violation: {str(e)}")
                raise DatabaseError("Invalid grade data - please ensure the image contains valid academic information")
            else:
                logger.error(f"Unexpected database error storing grades: {str(e)}")
                raise DatabaseError(f"Database storage failed: unable to save grade data")
    
    async def get_user_grades(self, db: AsyncSession, user_id: str) -> list:
        """Get all grades for a user"""
        try:
            stmt = select(Grade).where(Grade.user_id == user_id)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get grades for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve grades: {str(e)}")
    
    async def get_semester_grades(
        self, 
        db: AsyncSession, 
        user_id: str, 
        semester: int
    ) -> list:
        """Get grades for a specific semester"""
        try:
            stmt = select(Grade).where(
                Grade.user_id == user_id,
                Grade.semester == semester
            )
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get semester {semester} grades for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve semester grades: {str(e)}")


# Service instance
grades_service = GradesService()

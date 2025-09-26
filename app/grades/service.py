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

    async def delete_all_user_data(self, db: AsyncSession, user_id: str) -> Dict[str, Any]:
        """
        Delete all grades and uploads for a user (for testing/reset purposes)
        
        This is a comprehensive cleanup operation that removes:
        - All grade records for the user
        - All upload records for the user
        
        Returns summary of deleted records
        """
        try:
            # Get counts before deletion for reporting
            grades_stmt = select(Grade).where(Grade.user_id == user_id)
            uploads_stmt = select(GradeUpload).where(GradeUpload.user_id == user_id)
            
            grades_result = await db.execute(grades_stmt)
            uploads_result = await db.execute(uploads_stmt)
            
            grades_count = len(list(grades_result.scalars().all()))
            uploads_count = len(list(uploads_result.scalars().all()))
            
            if grades_count == 0 and uploads_count == 0:
                return {
                    "status": "no_data",
                    "message": "No grade data found for user",
                    "deleted_grades": 0,
                    "deleted_uploads": 0
                }
            
            # Delete all grades for the user using instance deletion for SQLModel compatibility
            grades_to_delete = await db.execute(select(Grade).where(Grade.user_id == user_id))
            for grade in grades_to_delete.scalars().all():
                await db.delete(grade)
            
            # Delete all uploads for the user
            uploads_to_delete = await db.execute(select(GradeUpload).where(GradeUpload.user_id == user_id))
            for upload in uploads_to_delete.scalars().all():
                await db.delete(upload)
            
            # Commit the transaction
            await db.commit()
            
            logger.info(f"Deleted all data for user {user_id}: {grades_count} grades, {uploads_count} uploads")
            
            return {
                "status": "success",
                "message": "Successfully deleted all grade data for user",
                "deleted_grades": grades_count,
                "deleted_uploads": uploads_count
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to delete user data for {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete user data: {str(e)}")
    
    async def delete_semester_data(
        self, 
        db: AsyncSession, 
        user_id: str, 
        semester: int
    ) -> Dict[str, Any]:
        """
        Delete all grades for a specific semester (granular testing control)
        
        This allows selective deletion of semester data while preserving other semesters
        """
        try:
            # Get grades for the specific semester
            grades_stmt = select(Grade).where(
                (Grade.user_id == user_id) & (Grade.semester == semester)
            )
            grades_result = await db.execute(grades_stmt)
            grades_to_delete = list(grades_result.scalars().all())
            grades_count = len(grades_to_delete)
            
            if grades_count == 0:
                return {
                    "status": "no_data",
                    "message": f"No grades found for semester {semester}",
                    "deleted_grades": 0,
                    "semester": semester
                }
            
            # Delete grades for the specific semester
            for grade in grades_to_delete:
                await db.delete(grade)
            
            await db.commit()
            
            logger.info(f"Deleted semester {semester} data for user {user_id}: {grades_count} grades")
            
            return {
                "status": "success",
                "message": f"Successfully deleted {grades_count} grades for semester {semester}",
                "deleted_grades": grades_count,
                "semester": semester
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to delete semester {semester} data for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete semester data: {str(e)}")
    
    async def delete_upload_data(
        self, 
        db: AsyncSession, 
        user_id: str, 
        upload_id: str
    ) -> Dict[str, Any]:
        """
        Delete upload record (precise testing control)
        
        This allows deletion of specific upload records for testing cleanup
        Note: Grade records don't currently track upload_id, so this only deletes the upload record
        """
        try:
            # Check if upload exists and belongs to user
            upload_stmt = select(GradeUpload).where(
                (GradeUpload.id == upload_id) & (GradeUpload.user_id == user_id)
            )
            upload_result = await db.execute(upload_stmt)
            upload_record = upload_result.scalar_one_or_none()
            
            if not upload_record:
                return {
                    "status": "not_found",
                    "message": f"Upload {upload_id} not found or doesn't belong to user",
                    "deleted_uploads": 0,
                    "upload_id": upload_id
                }
            
            # Delete the upload record
            await db.delete(upload_record)
            await db.commit()
            
            logger.info(f"Deleted upload record {upload_id} for user {user_id}")
            
            return {
                "status": "success",
                "message": "Successfully deleted upload record",
                "deleted_uploads": 1,
                "upload_id": upload_id
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to delete upload {upload_id} for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete upload data: {str(e)}")


# Service instance
grades_service = GradesService()

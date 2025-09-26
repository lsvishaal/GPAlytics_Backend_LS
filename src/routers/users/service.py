"""Users Service (feature-based)
Moved from app/features/users/service.py with adjusted imports
"""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from datetime import datetime, timezone
import logging

from ...shared.entities import User, Grade
from ...shared.exceptions import DatabaseError, ValidationError
from ...shared.security import hash_password

logger = logging.getLogger(__name__)


class UsersService:
    async def get_user_profile(self, db: AsyncSession, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by ID"""
        try:
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if not user:
                return None
            return {
                "id": user.id,
                "name": user.name,
                "regno": user.regno,
                "batch": user.batch,
                "created_at": user.created_at,
                "last_login": user.last_login,
                "updated_at": user.updated_at,
            }
        except Exception as e:
            logger.error(f"Failed to get user profile for {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve user profile: {str(e)}")
    
    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> Optional[User]:
        """Get user entity by ID"""
        try:
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user by id {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve user: {str(e)}")
    
    async def get_user_by_regno(self, db: AsyncSession, regno: str) -> Optional[User]:
        """Get user by registration number"""
        try:
            stmt = select(User).where(User.regno == regno.upper())
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user by regno {regno}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve user: {str(e)}")
    
    async def update_user_profile(self, db: AsyncSession, user_id: str, update_data: Dict[str, Any]) -> User:
        """Update user profile with provided data"""
        try:
            # Get existing user
            user = await self.get_user_by_id(db, user_id)
            if not user:
                raise ValidationError("User not found")
            
            # Update allowed fields
            if "name" in update_data:
                user.name = update_data["name"].strip()
            if "batch" in update_data:
                batch = update_data["batch"]
                if not isinstance(batch, int) or batch < 2015 or batch > 2045:
                    raise ValidationError("Invalid batch year")
                user.batch = batch
            
            # Update timestamp
            user.updated_at = datetime.now(timezone.utc)
            
            await db.commit()
            await db.refresh(user)
            
            logger.info(f"Updated profile for user {user_id}")
            return user
            
        except ValidationError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update user profile for {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to update user profile: {str(e)}")
    
    async def update_password(self, db: AsyncSession, user_id: str, new_password: str) -> bool:
        """Update user password"""
        try:
            user = await self.get_user_by_id(db, user_id)
            if not user:
                raise ValidationError("User not found")
            
            # Hash new password
            user.password_hash = hash_password(new_password)
            user.updated_at = datetime.now(timezone.utc)
            
            await db.commit()
            
            logger.info(f"Updated password for user {user_id}")
            return True
            
        except ValidationError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update password for {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to update password: {str(e)}")
    
    async def get_user_analytics(self, db: AsyncSession, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user analytics"""
        try:
            # Get user info
            user = await self.get_user_by_id(db, user_id)
            if not user:
                raise ValidationError("User not found")
            
            # Get all user grades
            stmt = select(Grade).where(Grade.user_id == user_id)
            result = await db.execute(stmt)
            grades = list(result.scalars().all())
            
            if not grades:
                return {
                    "current_gpa": 0.0,
                    "total_credits": 0,
                    "subjects_count": 0,
                    "semesters_completed": 0,
                    "average_credits_per_semester": 0.0,
                    "grade_distribution": {},
                    "academic_status": "No grades recorded"
                }
            
            # Calculate analytics
            total_credits = sum(grade.credits for grade in grades)
            total_points = sum(grade.gpa_points * grade.credits for grade in grades)
            current_gpa = total_points / total_credits if total_credits > 0 else 0.0
            
            # Semester analysis
            semesters = set(grade.semester for grade in grades)
            semesters_completed = len(semesters)
            avg_credits_per_sem = total_credits / semesters_completed if semesters_completed > 0 else 0.0
            
            # Grade distribution
            grade_dist = {}
            for grade in grades:
                grade_letter = grade.grade
                grade_dist[grade_letter] = grade_dist.get(grade_letter, 0) + 1
            
            # Academic status
            if current_gpa >= 9.0:
                status = "Outstanding"
            elif current_gpa >= 8.0:
                status = "Excellent"
            elif current_gpa >= 7.0:
                status = "Very Good"
            elif current_gpa >= 6.0:
                status = "Good"
            elif current_gpa >= 5.0:
                status = "Average"
            else:
                status = "Below Average"
            
            return {
                "current_gpa": round(current_gpa, 2),
                "total_credits": total_credits,
                "subjects_count": len(grades),
                "semesters_completed": semesters_completed,
                "average_credits_per_semester": round(avg_credits_per_sem, 2),
                "grade_distribution": grade_dist,
                "academic_status": status
            }
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get user analytics for {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve user analytics: {str(e)}")
    
    async def get_users_count(self, db: AsyncSession) -> int:
        """Get total number of registered users (admin function)"""
        try:
            stmt = select(func.count()).select_from(User)
            result = await db.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Failed to get users count: {str(e)}")
            raise DatabaseError(f"Failed to get users count: {str(e)}")
    
    async def delete_user_account(self, db: AsyncSession, user_id: str) -> bool:
        """Delete user account and all associated data"""
        try:
            user = await self.get_user_by_id(db, user_id)
            if not user:
                return False
            
            # Delete user (cascade should handle related records)
            await db.delete(user)
            await db.commit()
            
            logger.info(f"Deleted user account {user_id}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to delete user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete user account: {str(e)}")


users_service = UsersService()

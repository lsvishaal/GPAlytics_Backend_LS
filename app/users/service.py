"""
Users Service  
Business logic for user profile management
"""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import logging

from ..entities import User, UserPublicSchema
from ..core import DatabaseError

logger = logging.getLogger(__name__)


class UsersService:
    """User profile management business logic"""
    
    async def get_user_profile(self, db: AsyncSession, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile information"""
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
                "updated_at": user.updated_at
            }
            
        except Exception as e:
            logger.error(f"Failed to get user profile for {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve user profile: {str(e)}")


# Service instance
users_service = UsersService()

"""Users Service (feature-based)
Moved from app/features/users/service.py with adjusted imports
"""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import logging

from ...shared.entities import User
from ...shared.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class UsersService:
    async def get_user_profile(self, db: AsyncSession, user_id: str) -> Optional[Dict[str, Any]]:
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


users_service = UsersService()

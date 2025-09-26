"""Users API (feature-based)
Moved from app/features/users/api.py with adjusted imports
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ..auth import get_current_user
from ...shared.entities import User
from ...shared.database import get_db_session
from ...shared.exceptions import DatabaseError
from .service import users_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["User Profile"])


@router.get("/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        profile_data = await users_service.get_user_profile(db, current_user.id)
        if not profile_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
        return {"success": True, "message": "Profile retrieved successfully", "profile": profile_data}
    except DatabaseError:
        logger.exception("Profile retrieval failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve profile")

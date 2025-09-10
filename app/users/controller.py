"""
Users Controller
HTTP layer for user profile endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ..auth import get_current_user
from ..entities import User
from ..core import get_db_session, DatabaseError
from .service import users_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["User Profile"])


@router.get("/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    **Get User Profile**
    
    Retrieve current user's profile information.
    
    **Returns:**
    - User ID, name, registration number
    - Account creation and last login timestamps
    - Academic batch information
    """
    try:
        profile_data = await users_service.get_user_profile(db, current_user.id)
        
        if not profile_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return {
            "success": True,
            "message": "Profile retrieved successfully",
            "profile": profile_data
        }
        
    except DatabaseError as e:
        logger.error(f"Profile retrieval failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile"
        )

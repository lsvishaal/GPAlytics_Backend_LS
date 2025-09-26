"""Users API (feature-based)
Moved from app/features/users/api.py with adjusted imports
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import logging

from ..auth import get_current_user
from ...shared.entities import User, UserPublicSchema
from ...shared.database import get_db_session
from ...shared.exceptions import DatabaseError, ValidationError
from .service import users_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["👤 User Management"])


# Request/Response Schemas
class UserUpdateSchema(BaseModel):
    """Schema for updating user profile"""
    name: str = Field(min_length=1, max_length=100, description="Full name")
    batch: int = Field(ge=2015, le=2045, description="Academic batch year")


class PasswordUpdateSchema(BaseModel):
    """Schema for password update"""
    current_password: str = Field(min_length=8, max_length=100, description="Current password")
    new_password: str = Field(min_length=8, max_length=100, description="New password")


class UserAnalyticsResponse(BaseModel):
    """Schema for user analytics response"""
    current_gpa: float = Field(description="Current CGPA")
    total_credits: int = Field(description="Total credits completed")
    subjects_count: int = Field(description="Total number of subjects")
    semesters_completed: int = Field(description="Number of semesters completed")
    average_credits_per_semester: float = Field(description="Average credits per semester")
    grade_distribution: dict = Field(description="Grade distribution")
    academic_status: str = Field(description="Academic performance status")


@router.get(
    "/me",
    summary="🔍 Get Current User Profile",
    description="Retrieve the authenticated user's profile information",
    response_model=UserPublicSchema,
    responses={
        200: {"description": "User profile retrieved successfully"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"}
    }
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get current authenticated user's profile"""
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
            "user": profile_data
        }
        
    except DatabaseError:
        logger.exception("Profile retrieval failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to retrieve profile"
        )


@router.patch(
    "/me",
    summary="✏️ Update User Profile",
    description="Update the authenticated user's profile information",
    responses={
        200: {"description": "Profile updated successfully"},
        400: {"description": "Invalid data provided"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"}
    }
)
async def update_user_profile(
    update_data: UserUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Update current user's profile"""
    try:
        updated_user = await users_service.update_user_profile(
            db, current_user.id, update_data.dict()
        )
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "user": {
                "id": updated_user.id,
                "name": updated_user.name,
                "regno": updated_user.regno,
                "batch": updated_user.batch,
                "updated_at": updated_user.updated_at
            }
        }
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError:
        logger.exception("Profile update failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.patch(
    "/me/password",
    summary="🔒 Update Password",
    description="Update the authenticated user's password",
    responses={
        200: {"description": "Password updated successfully"},
        400: {"description": "Invalid current password"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"}
    }
)
async def update_password(
    password_data: PasswordUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Update user password"""
    try:
        from ...shared.security import verify_password
        
        # Verify current password
        if not verify_password(password_data.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        await users_service.update_password(db, current_user.id, password_data.new_password)
        
        return {
            "success": True,
            "message": "Password updated successfully"
        }
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError:
        logger.exception("Password update failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )


@router.get(
    "/me/analytics",
    summary="📊 Get User Analytics",
    description="Get comprehensive analytics for the authenticated user's academic performance",
    response_model=UserAnalyticsResponse,
    responses={
        200: {"description": "Analytics retrieved successfully"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"}
    }
)
async def get_user_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get user's academic analytics"""
    try:
        analytics = await users_service.get_user_analytics(db, current_user.id)
        
        return {
            "success": True,
            "message": "Analytics retrieved successfully",
            "user_info": {
                "id": current_user.id,
                "name": current_user.name,
                "regno": current_user.regno,
                "batch": current_user.batch
            },
            "analytics": analytics
        }
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError:
        logger.exception("Analytics retrieval failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics"
        )


@router.delete(
    "/me",
    summary="🗑️ Delete User Account",
    description="Permanently delete the authenticated user's account and all associated data",
    responses={
        200: {"description": "Account deleted successfully"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"}
    }
)
async def delete_user_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete user account (irreversible)"""
    try:
        deleted = await users_service.delete_user_account(db, current_user.id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account not found"
            )
        
        return {
            "success": True,
            "message": "Account deleted successfully. All your data has been permanently removed."
        }
        
    except DatabaseError:
        logger.exception("Account deletion failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )


# Legacy compatibility endpoint
@router.get(
    "/profile",
    summary="🔍 Get User Profile (Legacy)",
    description="Legacy endpoint for user profile (use /me instead)",
    deprecated=True,
    include_in_schema=False
)
async def get_user_profile_legacy(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Legacy profile endpoint - redirects to /me"""
    return await get_current_user_profile(current_user, db)

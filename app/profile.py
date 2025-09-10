"""
User profile and account management endpoints for GPAlytics
Clean user information retrieval with avatar generation
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from datetime import datetime
import hashlib

from .auth import get_current_user
from .models import User
from .database import get_db_session

logger = logging.getLogger(__name__)

# ==========================================
# AVATAR GENERATION
# ==========================================

def generate_profile_picture_url(regno: str, name: str) -> str:
    """
    Generate a consistent, deterministic profile picture URL
    Uses DiceBear API for beautiful, consistent avatars
    """
    try:
        # Create a deterministic seed from regno for consistency
        seed = hashlib.md5(regno.encode()).hexdigest()[:16]
        
        # DiceBear avatars - professional and consistent
        avatar_styles = [
            "avataaars",      # Human-like avatars
            "big-smile",      # Friendly cartoon style
            "lorelei",        # Professional illustrations
            "miniavs",        # Minimalist style
            "open-peeps"      # Hand-drawn style
        ]
        
        # Choose style based on batch year (from regno) for variety
        batch_indicator = int(regno[2:4]) if len(regno) >= 4 and regno[2:4].isdigit() else 0
        style = avatar_styles[batch_indicator % len(avatar_styles)]
        
        # Generate URL with consistent parameters
        base_url = f"https://api.dicebear.com/7.x/{style}/svg"
        params = f"seed={seed}&backgroundColor=b6e3f4,c0aede,d1d4f9,ffd5dc,ffdfbf"
        
        return f"{base_url}?{params}"
        
    except Exception as e:
        logger.warning(f"Avatar generation failed for {regno}: {str(e)}")
        # Fallback to simple initials-based avatar
        initials = "".join([part[0].upper() for part in name.split()[:2]]) if name else regno[:2].upper()
        return f"https://ui-avatars.com/api/?name={initials}&background=random&size=150"

def calculate_member_duration(created_at: datetime) -> dict:
    """
    Calculate how long the user has been a member
    Returns human-readable duration information
    """
    try:
        now = datetime.now(created_at.tzinfo) if created_at.tzinfo else datetime.utcnow()
        delta = now - created_at
        
        days = delta.days
        if days < 30:
            return {
                "duration": f"{days} day{'s' if days != 1 else ''}",
                "badge": "🌱 New Member" if days < 7 else "📚 Getting Started"
            }
        elif days < 365:
            months = days // 30
            return {
                "duration": f"{months} month{'s' if months != 1 else ''}",
                "badge": "🎓 Active Student"
            }
        else:
            years = days // 365
            remaining_months = (days % 365) // 30
            duration_str = f"{years} year{'s' if years != 1 else ''}"
            if remaining_months > 0:
                duration_str += f", {remaining_months} month{'s' if remaining_months != 1 else ''}"
            return {
                "duration": duration_str,
                "badge": "⭐ Veteran Member"
            }
            
    except Exception as e:
        logger.warning(f"Duration calculation failed: {str(e)}")
        return {
            "duration": "Unknown",
            "badge": "📚 Member"
        }

# ==========================================
# USER PROFILE ROUTER
# ==========================================

router = APIRouter(prefix="/user", tags=["User Profile"])

@router.get("/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get comprehensive user profile information
    
    Returns:
    - Basic user details (name, regno, batch)
    - Generated profile picture URL
    - Account information (member since, duration)
    - Academic status indicators
    """
    try:
        # Generate profile picture URL
        try:
            profile_picture = generate_profile_picture_url(current_user.regno, current_user.name)
        except Exception as e:
            logger.warning(f"Profile picture generation failed for {current_user.id}: {str(e)}")
            # Ultimate fallback
            profile_picture = f"https://ui-avatars.com/api/?name={current_user.name[:2].upper()}&background=4f46e5&color=ffffff&size=150"
        
        # Calculate membership duration
        try:
            member_info = calculate_member_duration(current_user.created_at)
        except Exception as e:
            logger.warning(f"Member duration calculation failed for {current_user.id}: {str(e)}")
            member_info = {"duration": "Member", "badge": "📚 Student"}
        
        # Get basic academic stats (gracefully handle failures)
        try:
            from .services import calculate_user_cgpa
            cgpa_data = await calculate_user_cgpa(db, current_user.id)
            academic_status = {
                "has_grades": cgpa_data["total_subjects"] > 0,
                "semesters_completed": cgpa_data["semesters_completed"],
                "total_subjects": cgpa_data["total_subjects"],
                "current_cgpa": cgpa_data["cgpa"] if cgpa_data["total_subjects"] > 0 else None
            }
        except Exception as e:
            logger.warning(f"Academic status calculation failed for {current_user.id}: {str(e)}")
            academic_status = {
                "has_grades": False,
                "semesters_completed": 0,
                "total_subjects": 0,
                "current_cgpa": None
            }
        
        # Build response
        response_data = {
            "success": True,
            "message": "Profile retrieved successfully",
            "profile": {
                # Basic Information
                "user_id": current_user.id,
                "name": current_user.name,
                "regno": current_user.regno,
                "batch": current_user.batch,
                
                # Visual & Identity
                "profile_picture": profile_picture,
                
                # Account Information
                "member_since": current_user.created_at.isoformat(),
                "member_duration": member_info["duration"],
                "member_badge": member_info["badge"],
                "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
                
                # Academic Overview
                "academic_status": academic_status
            }
        }
        
        logger.info(f"Profile retrieved successfully for user {current_user.id}")
        return response_data
        
    except Exception as e:
        logger.error(f"Profile retrieval failed for user {current_user.id}: {str(e)}")
        
        # Graceful fallback with minimal data
        try:
            fallback_avatar = f"https://ui-avatars.com/api/?name={current_user.name[:2].upper()}&background=6366f1&color=ffffff&size=150"
            
            return {
                "success": True,
                "message": "Profile retrieved with limited data due to processing issues",
                "profile": {
                    "user_id": current_user.id,
                    "name": current_user.name,
                    "regno": current_user.regno,
                    "batch": current_user.batch,
                    "profile_picture": fallback_avatar,
                    "member_since": current_user.created_at.isoformat() if current_user.created_at else None,
                    "member_duration": "Member",
                    "member_badge": "📚 Student",
                    "academic_status": {
                        "has_grades": False,
                        "semesters_completed": 0,
                        "total_subjects": 0,
                        "current_cgpa": None
                    }
                },
                "warning": "Some profile data could not be loaded. Please try again later."
            }
            
        except Exception as fallback_error:
            logger.error(f"Even fallback profile failed for user {current_user.id}: {str(fallback_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve profile information"
            )

@router.get("/settings")
async def get_user_settings(
    current_user: User = Depends(get_current_user)
):
    """
    Get user account settings and preferences
    Ready for future expansion (themes, notifications, etc.)
    """
    try:
        return {
            "success": True,
            "message": "User settings retrieved",
            "settings": {
                "user_id": current_user.id,
                "account": {
                    "regno": current_user.regno,
                    "name": current_user.name,
                    "batch": current_user.batch,
                    "email_verified": False,  # Future feature
                    "two_factor_enabled": False,  # Future feature
                },
                "preferences": {
                    "theme": "system",  # Future feature
                    "notifications": {
                        "grade_updates": True,
                        "performance_insights": True,
                        "system_announcements": True
                    }
                },
                "privacy": {
                    "profile_visibility": "private",
                    "grade_sharing": False
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Settings retrieval failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user settings"
        )

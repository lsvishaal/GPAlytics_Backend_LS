"""
Authentication Controller
HTTP layer for authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import logging

from ..core import get_db_session, decode_access_token, AuthenticationError, ValidationError
from ..entities import User, UserRegisterSchema, UserLoginSchema, ForgotPasswordSchema
from .service import auth_service

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@router.post("/register")
async def register(
    user_data: UserRegisterSchema, 
    db: AsyncSession = Depends(get_db_session)
):
    """
    **Register New User**
    
    Create a new user account with validation.
    
    **Request Body:**
    - `name`: Full name (1-100 characters)
    - `regno`: Registration number (exactly 15 characters)
    - `password`: Strong password (min 8 chars, mixed case, digit, special char)
    - `batch`: Graduation year (2015-2045)
    """
    try:
        result = await auth_service.register_user(db, user_data)
        return {"message": "Registration successful", **result}
    except (ValidationError, AuthenticationError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login")
async def login(
    credentials: UserLoginSchema, 
    db: AsyncSession = Depends(get_db_session)
):
    """
    **User Login**
    
    Authenticate user and return access token.
    
    **Request Body:**
    - `regno`: Registration number
    - `password`: User password
    """
    try:
        result = await auth_service.login_user(db, credentials)
        return {"message": "Login successful", **result}
    except AuthenticationError as e:
        # Provide specific authentication error message
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=str(e)
        )
    except ValidationError as e:
        # Provide specific validation error message  
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Login failed for {credentials.regno}: {str(e)}")
        logger.error(f"Login error type: {type(e).__name__}")
        import traceback
        logger.error(f"Login traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Authentication system error: {str(e)}")


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordSchema,
    db: AsyncSession = Depends(get_db_session)
):
    """
    **Reset Password**
    
    Reset password using registration number and name verification.
    
    **Request Body:**
    - `regno`: Registration number
    - `name`: Full name for verification
    - `new_password`: New password (must meet strength requirements)
    
    **Security Note:** This is a simplified implementation for development.
    In production, implement proper email/SMS verification.
    """
    try:
        result = await auth_service.reset_password(
            db, 
            request.regno,
            request.name, 
            request.new_password
        )
        return result
        
    except (AuthenticationError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Password reset failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Password reset failed")

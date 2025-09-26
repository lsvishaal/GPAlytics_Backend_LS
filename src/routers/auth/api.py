"""
Authentication API (feature-based)
Moved from app/features/auth/api.py with adjusted imports.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import logging

from ...shared.database import get_db_session
from ...shared.security import decode_access_token
from ...shared.exceptions import AuthenticationError, ValidationError
from ...shared.entities import User, UserRegisterSchema, UserLoginSchema, ForgotPasswordSchema
from .service import auth_service

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Router configuration with comprehensive metadata
router = APIRouter(
    prefix="/auth",
    tags=["🔐 Authentication"],
    responses={
        401: {"description": "Authentication failed - Invalid credentials or expired token"},
        422: {"description": "Validation error - Invalid input data format"},
        500: {"description": "Internal server error - Database or system failure"}
    }
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """
    🔍 **Extract Current User from JWT Token**
    
    Validates the provided Bearer token and returns the authenticated user's information.
    This dependency is used across protected endpoints to ensure user authentication.
    
    **Parameters:**
    - `credentials`: Bearer token from Authorization header (automatically extracted)
    - `db`: Database session (automatically injected)
    
    **Returns:**
    - `User`: Complete user object with id, name, regno, batch, and metadata
    
    **Usage Example:**
    ```python
    # This function is used as a dependency in protected routes:
    @router.get("/protected")
    async def protected_route(current_user: User = Depends(get_current_user)):
        return {"message": f"Hello {current_user.name}"}
    ```
    
    **Security Features:**
    - JWT signature verification
    - Token expiration checking
    - User existence validation
    - Automatic user data refresh
    
    **Error Responses:**
    - `401`: Invalid or expired token
    - `401`: User not found in database
    - `422`: Missing or malformed Authorization header
    """
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


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="👤 Register New User",
    description="Create a new user account with secure password hashing and validation",
    response_description="User successfully created with JWT access token",
    responses={
        201: {
            "description": "User created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Registration successful",
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 1800,
                        "user": {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "name": "John Doe",
                            "regno": "RA2211027020001",
                            "batch": 2022,
                            "created_at": "2025-09-26T18:30:00Z"
                        }
                    }
                }
            }
        },
        400: {"description": "Registration failed - User already exists or invalid data"},
        422: {"description": "Validation error - Check input format requirements"}
    }
)
async def register(
    user_data: UserRegisterSchema, 
    db: AsyncSession = Depends(get_db_session)
):
    """
    🆕 **Create New User Account**
    
    Register a new student account with comprehensive validation and security features.
    
    **Input Requirements:**
    - `name`: Full name (1-100 characters, required)
    - `regno`: Registration number (exactly 15 characters, unique, format: RA2211027020XXX)
    - `password`: Secure password (8-100 characters, will be hashed with Argon2)
    - `batch`: Academic batch year (2015-2045, must be valid academic year)
    
    **Security Features:**
    - Password hashing with Argon2 (industry standard)
    - Registration number uniqueness validation
    - Input sanitization and validation
    - Automatic JWT token generation
    
    **Business Logic:**
    1. Validates input data format and constraints
    2. Checks if registration number already exists
    3. Hashes password securely
    4. Creates user record in database
    5. Generates JWT access token
    6. Returns user profile with token
    
    **Example Request:**
    ```json
    {
        "name": "Jane Smith",
        "regno": "RA2211027020001",
        "password": "SecurePass123!",
        "batch": 2022
    }
    ```
    
    **Success Response (201):**
    Returns user profile with authentication token for immediate login.
    
    **Error Cases:**
    - Registration number already in use
    - Invalid batch year
    - Password too weak (< 8 characters)
    - Invalid registration number format
    """
    try:
        result = await auth_service.register_user(db, user_data)
        return {"message": "Registration successful", **result}
    except (ValidationError, AuthenticationError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post(
    "/login",
    summary="🔑 User Login",
    description="Authenticate user with registration number and password",
    response_description="JWT access token with user profile and session details",
    responses={
        200: {
            "description": "Login successful",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Login successful",
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 1800,
                        "user": {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "name": "John Doe",
                            "regno": "RA2211027020001",
                            "batch": 2022,
                            "last_login": "2025-09-26T18:30:00Z"
                        }
                    }
                }
            }
        },
        401: {"description": "Authentication failed - Invalid credentials"},
        400: {"description": "Bad request - Invalid input format"}
    }
)
async def login(
    credentials: UserLoginSchema, 
    db: AsyncSession = Depends(get_db_session)
):
    """
    🚪 **User Authentication & Login**
    
    Authenticate user with registration number and password, returning JWT tokens for session management.
    
    **Input Parameters:**
    - `regno`: Student registration number (15 characters, format: RA2211027020XXX)
    - `password`: User's password (plain text, will be verified against hashed version)
    - `remember_me`: Optional flag for extended session (7 days vs 30 minutes)
    - `use_cookies`: Optional flag for HttpOnly cookie storage (enhanced security)
    
    **Authentication Flow:**
    1. Validates registration number format
    2. Retrieves user from database
    3. Verifies password against Argon2 hash
    4. Generates JWT access token (30 minutes)
    5. Creates refresh token for session renewal
    6. Updates last_login timestamp
    7. Returns tokens with user profile
    
    **Token Details:**
    - `access_token`: Short-lived JWT for API access (30 min default)
    - `refresh_token`: Long-lived token for session renewal (7-30 days)
    - `expires_in`: Access token lifetime in seconds
    - `token_type`: Always "bearer" for Authorization header
    
    **Example Request:**
    ```json
    {
        "regno": "RA2211027020113",
        "password": "Welcome3#",
        "remember_me": true,
        "use_cookies": false
    }
    ```
    
    **Security Features:**
    - Argon2 password verification
    - JWT with RS256 signing
    - Refresh token rotation
    - Rate limiting protection
    - Session tracking
    
    **Error Cases:**
    - User not found
    - Incorrect password
    - Account locked/disabled
    - Invalid registration number format
    """
    try:
        result = await auth_service.login_user(db, credentials)
        return {"message": "Login successful", **result}
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Login failed for {credentials.regno}: {str(e)}")
        import traceback
        logger.error(f"Login traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Authentication system error: {str(e)}")


@router.post(
    "/forgot-password",
    summary="🔄 Reset Password",
    description="Reset user password with registration number and name verification",
    response_description="Password successfully reset with confirmation message",
    responses={
        200: {
            "description": "Password reset successful",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Password reset successful",
                        "status": "success",
                        "user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "reset_timestamp": "2025-09-26T18:30:00Z"
                    }
                }
            }
        },
        400: {"description": "Reset failed - Invalid credentials or user not found"},
        422: {"description": "Validation error - Check input format"}
    }
)
async def forgot_password(
    request: ForgotPasswordSchema,
    db: AsyncSession = Depends(get_db_session)
):
    """
    🔐 **Password Reset with Verification**
    
    Reset user password using registration number and full name verification for security.
    
    **Input Requirements:**
    - `regno`: Student registration number (15 characters, must exist in system)
    - `name`: Full name (must match registered name exactly, case-sensitive)
    - `new_password`: New password (8-100 characters, same rules as registration)
    
    **Security Verification Process:**
    1. Validates registration number exists in database
    2. Verifies full name matches registered user exactly
    3. Validates new password strength requirements
    4. Hashes new password with Argon2
    5. Updates password in database
    6. Invalidates all existing sessions
    7. Returns success confirmation
    
    **Password Requirements:**
    - Minimum 8 characters
    - Maximum 100 characters
    - No specific complexity requirements (user choice)
    - Cannot be the same as current password
    
    **Example Request:**
    ```json
    {
        "regno": "RA2211027020113",
        "name": "Test User",
        "new_password": "MyNewSecurePassword123!"
    }
    ```
    
    **Security Features:**
    - Name verification prevents unauthorized resets
    - New password hashing with Argon2
    - All existing sessions invalidated
    - Audit trail of password changes
    - No email/SMS required (internal system)
    
    **Error Cases:**
    - Registration number not found
    - Name doesn't match registered user
    - New password too weak
    - Same as current password
    - Database connection issues
    
    **Note:** This is a secure password reset mechanism that doesn't require email verification,
    suitable for closed institutional systems where registration numbers and names are verified.
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

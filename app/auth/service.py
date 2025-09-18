"""
Authentication Service
Pure business logic for user authentication
"""
from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core import (
    hash_password, 
    verify_password, 
    create_access_token,
    AuthenticationError,
    ValidationError
)
from ..entities import User, UserRegisterSchema, UserLoginSchema, UserPublicSchema, TokenSchema


class AuthService:
    """Authentication business logic"""
    
    @staticmethod
    def validate_regno(regno: str) -> Optional[str]:
        """Validate registration number format"""
        if len(regno) != 15:
            return "Registration number must be 15 characters"
        if not regno[:2].isalpha() or not regno[:2].isupper():
            return "First 2 characters must be uppercase letters"
        if not regno[2:].isdigit():
            return "Last 13 characters must be digits"
        return None
    
    @staticmethod
    def validate_password(password: str) -> Optional[str]:
        """Validate password strength"""
        if len(password) < 8:
            return "Password must be at least 8 characters"
        if not any(c.isupper() for c in password):
            return "Password must contain uppercase letter"
        if not any(c.islower() for c in password):
            return "Password must contain lowercase letter"
        if not any(c.isdigit() for c in password):
            return "Password must contain digit"
        if not any(not c.isalnum() for c in password):
            return "Password must contain special character"
        return None
    
    @staticmethod
    async def get_user_by_regno(db: AsyncSession, regno: str) -> Optional[User]:
        """Get user by registration number"""
        try:
            statement = select(User).where(User.regno == regno.upper())
            result = await db.execute(statement)
            return result.scalar_one_or_none()
        except Exception:
            return None
    
    async def register_user(self, db: AsyncSession, user_data: UserRegisterSchema) -> dict:
        """Register new user"""
        
        # Validate registration number
        if error := self.validate_regno(user_data.regno):
            raise ValidationError(error)
        
        # Validate password
        if error := self.validate_password(user_data.password):
            raise ValidationError(error)
        
        # Check if user exists
        if await self.get_user_by_regno(db, user_data.regno):
            raise ValidationError("User already exists")
        
        # Create user
        db_user = User(
            name=user_data.name.strip(),
            regno=user_data.regno.upper(),
            batch=user_data.batch,
            password_hash=hash_password(user_data.password)
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        # Create token
        token_data = {
            "sub": db_user.id,
            "regno": db_user.regno,
            "name": db_user.name,
            "batch": db_user.batch
        }
        access_token = create_access_token(token_data)
        
        return {
            "user": UserPublicSchema(
                id=db_user.id,
                name=db_user.name,
                regno=db_user.regno,
                batch=db_user.batch,
                created_at=db_user.created_at,
                last_login=db_user.last_login
            ),
            "token": TokenSchema(
                access_token=access_token,
                expires_in=30 * 60  # 30 minutes
            )
        }
    
    async def login_user(self, db: AsyncSession, credentials: UserLoginSchema) -> dict:
        """Authenticate user and return token with optional extended expiration"""
        
        try:
            user = await self.get_user_by_regno(db, credentials.regno)
            if not user or not verify_password(credentials.password, user.password_hash):
                raise AuthenticationError("Invalid credentials")
            
            # Update last login
            user.last_login = datetime.now(timezone.utc)
            await db.commit()
            
            # Determine token expiration based on remember_me flag
            if credentials.remember_me:
                # Extended session: 7 days
                expires_delta = timedelta(days=7)
                expires_in_seconds = 7 * 24 * 60 * 60  # 7 days in seconds
            else:
                # Standard session: 30 minutes
                expires_delta = None  # Use default from settings
                expires_in_seconds = 30 * 60  # 30 minutes in seconds
            
            # Create token with appropriate expiration
            token_data = {
                "sub": user.id,
                "regno": user.regno,
                "name": user.name,
                "batch": user.batch
            }
            access_token = create_access_token(token_data, expires_delta)
            
            return {
                "user": UserPublicSchema(
                    id=user.id,
                    name=user.name,
                    regno=user.regno,
                    batch=user.batch,
                    created_at=user.created_at,
                    last_login=user.last_login
                ),
                "token": TokenSchema(
                    access_token=access_token,
                    expires_in=expires_in_seconds
                ),
                "remember_me": credentials.remember_me
            }
        except Exception as e:
            # Ensure we rollback on any error
            await db.rollback()
            if isinstance(e, AuthenticationError):
                raise e
            else:
                raise AuthenticationError(f"Login failed: {str(e)}")
    
    async def reset_password(self, db: AsyncSession, regno: str, name: str, new_password: str) -> dict:
        """Reset user password with regno + name verification"""
        
        # Validate new password
        if error := self.validate_password(new_password):
            raise ValidationError(error)
        
        # Find user by regno
        user = await self.get_user_by_regno(db, regno)
        if not user:
            raise AuthenticationError("User not found")
        
        # Verify name matches (simple identity verification)
        if user.name.lower() != name.lower():
            raise AuthenticationError("Name doesn't match our records")
        
        # Update password
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Password reset successful. You can now login with your new password.",
            "regno": regno
        }


# Service instance
auth_service = AuthService()

"""
Refresh Token Service
Business logic for refresh token management
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, delete
import logging

from ..core import (
    settings,
    create_refresh_token, 
    decode_refresh_token,
    hash_refresh_token,
    verify_refresh_token_hash,
    create_access_token,
    AuthenticationError
)
from ..entities import RefreshToken, User

logger = logging.getLogger(__name__)


class RefreshTokenService:
    """Refresh token management business logic"""
    
    async def create_refresh_token(
        self, 
        db: AsyncSession, 
        user_id: str
    ) -> str:
        """Create and store a new refresh token"""
        try:
            # Generate JWT refresh token
            refresh_token = create_refresh_token(
                user_id, 
                expires_days=settings.refresh_token_expire_days
            )
            
            # Hash token for database storage
            token_hash = hash_refresh_token(refresh_token)
            
            # Calculate expiration
            expires_at = datetime.now(timezone.utc) + timedelta(
                days=settings.refresh_token_expire_days
            )
            
            # Store in database
            db_refresh_token = RefreshToken(
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at
            )
            
            db.add(db_refresh_token)
            await db.flush()  # Get the ID without committing
            
            logger.info(f"Created refresh token for user {user_id}")
            return refresh_token
            
        except Exception as e:
            logger.error(f"Failed to create refresh token for user {user_id}: {str(e)}")
            raise AuthenticationError("Failed to create refresh token")
    
    async def validate_and_rotate_token(
        self, 
        db: AsyncSession, 
        refresh_token: str
    ) -> Dict[str, Any]:
        """Validate refresh token and create new tokens (token rotation)"""
        try:
            # Decode and validate JWT
            payload = decode_refresh_token(refresh_token)
            if not payload:
                raise AuthenticationError("Invalid refresh token")
            
            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationError("Invalid token payload")
            
            # Hash the token to find in database
            token_hash = hash_refresh_token(refresh_token)
            
            # Find and validate stored token
            stmt = select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc)
            )
            result = await db.execute(stmt)
            db_token = result.scalar_one_or_none()
            
            if not db_token or db_token.user_id != user_id:
                raise AuthenticationError("Refresh token not found or expired")
            
            # Get user information
            user_stmt = select(User).where(User.id == user_id)
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if not user:
                raise AuthenticationError("User not found")
            
            # Revoke the old refresh token (single-use)
            db_token.is_revoked = True
            
            # Create new access token
            token_data = {
                "sub": user.id,
                "regno": user.regno,
                "name": user.name,
                "batch": user.batch
            }
            new_access_token = create_access_token(token_data)
            
            # Create new refresh token
            new_refresh_token = await self.create_refresh_token(db, user.id)
            
            # Commit all changes
            await db.commit()
            
            logger.info(f"Rotated refresh token for user {user_id}")
            
            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": settings.jwt_expire_minutes * 60,
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "regno": user.regno,
                    "batch": user.batch
                }
            }
            
        except AuthenticationError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Token rotation failed: {str(e)}")
            raise AuthenticationError("Token refresh failed")
    
    async def revoke_user_tokens(
        self, 
        db: AsyncSession, 
        user_id: str
    ) -> None:
        """Revoke all refresh tokens for a user (logout all devices)"""
        try:
            # Update all user's tokens to revoked
            stmt = (
                select(RefreshToken)
                .where(RefreshToken.user_id == user_id)
                .where(RefreshToken.is_revoked == False)
            )
            result = await db.execute(stmt)
            tokens = result.scalars().all()
            
            revoked_count = 0
            for token in tokens:
                token.is_revoked = True
                revoked_count += 1
            
            await db.commit()
            logger.info(f"Revoked {revoked_count} refresh tokens for user {user_id}")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to revoke tokens for user {user_id}: {str(e)}")
            raise AuthenticationError("Failed to revoke tokens")
    
    async def revoke_token(
        self, 
        db: AsyncSession, 
        refresh_token: str
    ) -> None:
        """Revoke a specific refresh token"""
        try:
            token_hash = hash_refresh_token(refresh_token)
            
            stmt = select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked == False
            )
            result = await db.execute(stmt)
            db_token = result.scalar_one_or_none()
            
            if db_token:
                db_token.is_revoked = True
                await db.commit()
                logger.info(f"Revoked refresh token for user {db_token.user_id}")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to revoke token: {str(e)}")
            # Don't raise error for token revocation failures
    
    async def cleanup_expired_tokens(self, db: AsyncSession) -> int:
        """Remove expired refresh tokens from database"""
        try:
            # Delete expired tokens
            stmt = delete(RefreshToken).where(
                RefreshToken.expires_at < datetime.now(timezone.utc)
            )
            result = await db.execute(stmt)
            deleted_count = result.rowcount or 0
            
            await db.commit()
            logger.info(f"Cleaned up {deleted_count} expired refresh tokens")
            
            return deleted_count
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Token cleanup failed: {str(e)}")
            return 0


# Service instance
refresh_token_service = RefreshTokenService()
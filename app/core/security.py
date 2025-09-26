"""
Core Security Utilities
JWT token management and password hashing
"""
from typing import Optional
from datetime import datetime, timezone, timedelta
import jwt
import hashlib
import secrets
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from .config import settings


# Password hasher instance
pwd_context = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash password using Argon2"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        pwd_context.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token with optional custom expiration"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_str, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_str, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.PyJWTError:
        return None


def create_refresh_token(user_id: str, expires_days: int = 30) -> str:
    """Create JWT refresh token with longer expiration"""
    expires_delta = timedelta(days=expires_days)
    expire = datetime.now(timezone.utc) + expires_delta
    data = {
        "sub": user_id,
        "type": "refresh",  # Token type identifier
        "jti": secrets.token_urlsafe(32),  # Unique token ID
        "exp": expire
    }
    return jwt.encode(data, settings.jwt_secret_str, algorithm=settings.jwt_algorithm)


def decode_refresh_token(token: str) -> Optional[dict]:
    """Decode and validate JWT refresh token"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_str, algorithms=[settings.jwt_algorithm])
        # Verify this is a refresh token
        if payload.get("type") != "refresh":
            return None
        return payload
    except jwt.PyJWTError:
        return None


def hash_refresh_token(token: str) -> str:
    """Hash refresh token for secure database storage"""
    return hashlib.sha256(token.encode()).hexdigest()


def verify_refresh_token_hash(token: str, token_hash: str) -> bool:
    """Verify refresh token against stored hash"""
    return hashlib.sha256(token.encode()).hexdigest() == token_hash

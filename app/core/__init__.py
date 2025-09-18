"""
Core package initialization
"""
from .config import settings
from .database import db_manager, get_db_session
from .security import (
    hash_password, 
    verify_password, 
    create_access_token, 
    decode_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_refresh_token,
    verify_refresh_token_hash
)
from .exceptions import (
    GPAlyticsException,
    AuthenticationError, 
    ValidationError,
    DatabaseError,
    OCRProcessingError,
    FileValidationError,
    http_authentication_error,
    http_validation_error,
    http_not_found_error,
    http_server_error
)

__all__ = [
    # Config
    "settings",
    
    # Database
    "db_manager", 
    "get_db_session",
    
    # Security
    "hash_password",
    "verify_password", 
    "create_access_token",
    "decode_access_token",
    "create_refresh_token",
    "decode_refresh_token", 
    "hash_refresh_token",
    "verify_refresh_token_hash",
    
    # Exceptions
    "GPAlyticsException",
    "AuthenticationError",
    "ValidationError", 
    "DatabaseError",
    "OCRProcessingError",
    "FileValidationError",
    "http_authentication_error",
    "http_validation_error",
    "http_not_found_error", 
    "http_server_error"
]

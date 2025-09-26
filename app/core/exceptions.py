"""
Core Custom Exceptions
Application-specific exceptions for better error handling
"""
from fastapi import HTTPException, status


class GPAlyticsException(Exception):
    """Base exception for GPAlytics application"""
    pass


class AuthenticationError(GPAlyticsException):
    """Authentication related errors"""
    pass


class ValidationError(GPAlyticsException):
    """Data validation errors"""
    pass


class DatabaseError(GPAlyticsException):
    """Database operation errors"""
    pass


class OCRProcessingError(GPAlyticsException):
    """OCR processing errors"""
    pass


class FileValidationError(GPAlyticsException):
    """File upload validation errors"""
    pass


# HTTP Exception Factories
def http_authentication_error(detail: str = "Authentication failed") -> HTTPException:
    """Create HTTP 401 exception"""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"}
    )


def http_validation_error(detail: str = "Validation failed") -> HTTPException:
    """Create HTTP 400 exception"""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail
    )


def http_not_found_error(detail: str = "Resource not found") -> HTTPException:
    """Create HTTP 404 exception"""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail
    )


def http_server_error(detail: str = "Internal server error") -> HTTPException:
    """Create HTTP 500 exception"""
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail
    )

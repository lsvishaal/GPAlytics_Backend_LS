"""
Authentication package initialization
"""
from .controller import router, get_current_user
from .service import auth_service

__all__ = [
    "router",
    "get_current_user", 
    "auth_service"
]

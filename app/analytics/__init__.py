"""
Analytics package initialization
"""
from .controller import router
from .service import analytics_service

__all__ = [
    "router",
    "analytics_service"
]

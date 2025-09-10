"""
Grades package initialization
"""
from .controller import router
from .service import grades_service
from .ocr import ocr_service

__all__ = [
    "router",
    "grades_service", 
    "ocr_service"
]

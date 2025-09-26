"""Test utilities and helpers"""
from typing import Dict, Any, Optional
import uuid
from src.shared.entities import User, Grade
from src.shared.security import hash_password


def create_test_user_data(regno: Optional[str] = None) -> Dict[str, Any]:
    """Create test user registration data"""
    if not regno:
        regno = f"RA2211027{str(uuid.uuid4())[:6]}"
    
    return {
        "name": "Test User",
        "regno": regno,
        "password": "TestPass123!",
        "batch": 2022
    }


def create_test_grade_data(user_id: str, semester: int = 1) -> Dict[str, Any]:
    """Create test grade data"""
    return {
        "user_id": user_id,
        "course_name": "Test Course",
        "course_code": "TEST101",
        "credits": 3,
        "grade": "A",
        "semester": semester,
        "gpa_points": 9.0
    }


class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_user(regno: Optional[str] = None, **kwargs) -> User:
        """Create User instance for testing"""
        defaults = {
            "name": "Test User",
            "regno": regno or f"RA2211027{str(uuid.uuid4())[:6]}",
            "password_hash": hash_password("testpass123"),
            "batch": 2022
        }
        defaults.update(kwargs)
        return User(**defaults)
    
    @staticmethod
    def create_grade(user_id: str, **kwargs) -> Grade:
        """Create Grade instance for testing"""
        defaults = {
            "user_id": user_id,
            "course_name": "Test Course",
            "course_code": "TEST101",
            "credits": 3,
            "grade": "A",
            "semester": 1,
            "gpa_points": 9.0
        }
        defaults.update(kwargs)
        return Grade(**defaults)

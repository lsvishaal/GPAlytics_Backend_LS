"""Unit tests for user management service"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.routers.users.service import users_service
from tests.utils import TestDataFactory


class TestUsersService:
    """Test user management service methods"""
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self):
        """Test getting user by ID when user exists"""
        mock_db = AsyncMock(spec=AsyncSession)
        expected_user = TestDataFactory.create_user(id="1", regno="RA2211027123456")
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected_user
        mock_db.execute.return_value = mock_result
        
        result = await users_service.get_user_by_id(mock_db, "1")
        
        assert result == expected_user
        mock_db.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self):
        """Test getting user by ID when user doesn't exist"""
        mock_db = AsyncMock(spec=AsyncSession)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        result = await users_service.get_user_by_id(mock_db, "999")
        
        assert result is None
        mock_db.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_user_profile_success(self):
        """Test successful user profile update"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_id = "1"
        update_data = {"name": "Updated Name", "batch": 2023}
        
        mock_user = TestDataFactory.create_user(id=user_id, name="Old Name", batch=2022)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        
        result = await users_service.update_user_profile(mock_db, user_id, update_data)
        
        assert result.name == update_data["name"]
        assert result.batch == update_data["batch"]
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_user)
    
    @pytest.mark.asyncio
    async def test_get_user_analytics_success(self):
        """Test getting user analytics data"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_id = "1"
        
        # Mock grades for the user
        mock_grades = [
            TestDataFactory.create_grade(user_id=user_id, grade="A+", credits=4),
            TestDataFactory.create_grade(user_id=user_id, grade="A", credits=3),
            TestDataFactory.create_grade(user_id=user_id, grade="B+", credits=3)
        ]
        
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = mock_grades
        mock_db.execute.return_value = mock_result
        
        result = await users_service.get_user_analytics(mock_db, user_id)
        
        assert "current_gpa" in result
        assert "total_credits" in result
        assert "subjects_count" in result
        assert result["total_credits"] == 10  # 4 + 3 + 3
        assert result["subjects_count"] == 3
    
    @pytest.mark.asyncio
    async def test_get_user_analytics_no_grades(self):
        """Test getting analytics for user with no grades"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_id = "1"
        
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []
        mock_db.execute.return_value = mock_result
        
        result = await users_service.get_user_analytics(mock_db, user_id)
        
        assert result["current_gpa"] == 0.0
        assert result["total_credits"] == 0
        assert result["subjects_count"] == 0

"""Unit tests for grade processing service"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.routers.grades.service import grades_service
from tests.utils import TestDataFactory


class TestGradesService:
    """Test grade processing service methods"""
    
    @pytest.mark.asyncio
    async def test_process_grade_sheet_success(self):
        """Test successful grade sheet processing"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user_id = 1
        mock_file_path = "/tmp/test_grade_sheet.jpg"
        
        expected_grades = [
            {"subject": "Mathematics", "grade": "A+", "credits": 4},
            {"subject": "Physics", "grade": "A", "credits": 3}
        ]
        
        # Mock OCR processing
        with patch('src.routers.grades.service.process_ocr') as mock_ocr:
            mock_ocr.return_value = expected_grades
            
            result = await grades_service.process_grade_sheet(
                mock_db, mock_user_id, mock_file_path
            )
            
            assert result["status"] == "completed"
            assert len(result["grades"]) == 2
            assert result["grades"][0]["subject"] == "Mathematics"
            mock_ocr.assert_called_once_with(mock_file_path)
    
    @pytest.mark.asyncio
    async def test_get_user_grades_success(self):
        """Test getting user grades from database"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user_id = 1
        
        expected_grades = [
            TestDataFactory.create_grade(user_id=mock_user_id, subject="Math"),
            TestDataFactory.create_grade(user_id=mock_user_id, subject="Physics")
        ]
        
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = expected_grades
        mock_db.execute.return_value = mock_result
        
        result = await grades_service.get_user_grades(mock_db, mock_user_id)
        
        assert len(result) == 2
        assert result[0].subject == "Math"
        assert result[1].subject == "Physics"
        mock_db.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_calculate_gpa_success(self):
        """Test GPA calculation from grades"""
        grades = [
            TestDataFactory.create_grade(grade="A+", credits=4),  # 10 * 4 = 40
            TestDataFactory.create_grade(grade="A", credits=3),   # 9 * 3 = 27
            TestDataFactory.create_grade(grade="B+", credits=3),  # 8 * 3 = 24
        ]
        
        gpa = grades_service.calculate_gpa(grades)
        
        # (40 + 27 + 24) / (4 + 3 + 3) = 91 / 10 = 9.1
        assert gpa == 9.1
    
    @pytest.mark.asyncio
    async def test_calculate_gpa_no_grades(self):
        """Test GPA calculation with no grades returns 0"""
        gpa = grades_service.calculate_gpa([])
        assert gpa == 0.0
    
    @pytest.mark.asyncio
    async def test_delete_grade_success(self):
        """Test successful grade deletion"""
        mock_db = AsyncMock(spec=AsyncSession)
        grade_id = 1
        user_id = 1
        
        mock_grade = TestDataFactory.create_grade(id=grade_id, user_id=user_id)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_grade
        mock_db.execute.return_value = mock_result
        
        result = await grades_service.delete_grade(mock_db, grade_id, user_id)
        
        assert result is True
        mock_db.delete.assert_called_once_with(mock_grade)
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_grade_fails(self):
        """Test deleting non-existent grade returns False"""
        mock_db = AsyncMock(spec=AsyncSession)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        result = await grades_service.delete_grade(mock_db, 999, 1)
        
        assert result is False
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()

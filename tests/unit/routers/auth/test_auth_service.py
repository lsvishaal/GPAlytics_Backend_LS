"""Unit tests for authentication service"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.routers.auth.service import auth_service
from src.shared.entities import UserLoginSchema, UserRegisterSchema
from tests.utils import TestDataFactory


class TestAuthService:
    """Test authentication service methods"""
    
    async def test_register_user_success(self, db_session: AsyncSession):
        """Test successful user registration"""
        user_data = UserRegisterSchema(
            name="Test User",
            regno="RA2211027123456",
            password="TestPass123!",
            batch=2022
        )
        
        # Mock the actual registration process
        with patch.object(auth_service, 'register_user') as mock_register:
            expected_result = {
                "id": 1,
                "regno": user_data.regno,
                "name": user_data.name,
                "batch": user_data.batch
            }
            mock_register.return_value = expected_result
            
            result = await auth_service.register_user(db_session, user_data)
            
            assert result["regno"] == user_data.regno
            assert result["name"] == user_data.name
            assert result["batch"] == user_data.batch
            assert "id" in result
    
    @pytest.mark.asyncio
    async def test_login_user_success(self):
        """Test successful user login"""
        # Create mock database session and user
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = TestDataFactory.create_user(
            regno="RA2211027123456",
            password_hash="$argon2id$v=19$m=65536,t=3,p=4$hashed_password"
        )
        
        # Mock database query to return user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        
        # Mock password verification
        with patch('src.routers.auth.service.verify_password', return_value=True):
            login_data = UserLoginSchema(
                regno="RA2211027123456",
                password="testpass123",
                remember_me=False,
                use_cookies=False
            )
            
            result = await auth_service.login_user(mock_db, login_data)
            
            assert result["user"].regno == login_data.regno
            assert "access_token" in result
            assert "refresh_token" in result
            assert result["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_user_invalid_password(self):
        """Test login fails with invalid password"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_user = TestDataFactory.create_user(regno="RA2211027123456")
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        
        # Mock password verification to fail
        with patch('src.routers.auth.service.verify_password', return_value=False):
            with pytest.raises(Exception) as exc_info:
                login_data = UserLoginSchema(
                    regno="RA2211027123456",
                    password="wrongpassword",
                    remember_me=False,
                    use_cookies=False
                )
                
                await auth_service.login_user(mock_db, login_data)
            
            assert "Invalid credentials" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_user_by_regno_found(self):
        """Test getting user by regno when user exists"""
        mock_db = AsyncMock(spec=AsyncSession)
        expected_user = TestDataFactory.create_user(regno="RA2211027123456")
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected_user
        mock_db.execute.return_value = mock_result
        
        result = await auth_service.get_user_by_regno(mock_db, "RA2211027123456")
        
        assert result == expected_user
        mock_db.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_by_regno_not_found(self):
        """Test getting user by regno when user doesn't exist"""
        mock_db = AsyncMock(spec=AsyncSession)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        result = await auth_service.get_user_by_regno(mock_db, "RA2211027000000")
        
        assert result is None
        mock_db.execute.assert_called_once()

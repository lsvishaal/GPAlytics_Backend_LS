"""Integration tests for authentication API endpoints"""
from httpx import AsyncClient

from tests.utils import create_test_user_data


class TestAuthRegistration:
    """Test user registration endpoint"""
    
    async def test_register_new_user_success(self, client: AsyncClient):
        """Test successful user registration"""
        user_data = create_test_user_data()
        
        response = await client.post("/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["regno"] == user_data["regno"]
        assert data["name"] == user_data["name"]
        assert "id" in data
        assert "password" not in data  # Ensure password not returned
    
    async def test_register_duplicate_regno_fails(self, client: AsyncClient, test_user):
        """Test registration fails with duplicate regno"""
        user_data = create_test_user_data(regno=test_user.regno)
        
        response = await client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    async def test_register_invalid_data_fails(self, client: AsyncClient):
        """Test registration fails with invalid data"""
        invalid_data = {
            "name": "",  # Empty name
            "regno": "invalid",  # Invalid format
            "password": "123",  # Too short
            "batch": 2050  # Invalid year
        }
        
        response = await client.post("/auth/register", json=invalid_data)
        
        assert response.status_code == 422


class TestAuthLogin:
    """Test user login endpoint"""
    
    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login"""
        login_data = {
            "regno": test_user.regno,
            "password": "testpass123",
            "remember_me": False,
            "use_cookies": False
        }
        
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["regno"] == test_user.regno
    
    async def test_login_invalid_credentials_fails(self, client: AsyncClient, test_user):
        """Test login fails with wrong password"""
        login_data = {
            "regno": test_user.regno,
            "password": "wrongpassword",
            "remember_me": False,
            "use_cookies": False
        }
        
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    async def test_login_nonexistent_user_fails(self, client: AsyncClient):
        """Test login fails with non-existent user"""
        login_data = {
            "regno": "RA2211027000000",
            "password": "testpass123",
            "remember_me": False,
            "use_cookies": False
        }
        
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]


class TestAuthProtected:
    """Test protected endpoints requiring authentication"""
    
    async def test_get_current_user_success(self, client: AsyncClient, auth_headers, test_user):
        """Test getting current user with valid token"""
        response = await client.get("/users/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["regno"] == test_user.regno
        assert data["name"] == test_user.name
    
    async def test_protected_endpoint_without_auth_fails(self, client: AsyncClient):
        """Test protected endpoint fails without authentication"""
        response = await client.get("/users/me")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

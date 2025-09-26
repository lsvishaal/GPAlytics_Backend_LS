"""Integration tests for user management API endpoints"""
from httpx import AsyncClient


class TestUserProfile:
    """Test user profile management endpoints"""
    
    async def test_get_current_user_success(self, client: AsyncClient, auth_headers, test_user):
        """Test getting current user profile"""
        response = await client.get("/users/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["regno"] == test_user.regno
        assert data["name"] == test_user.name
        assert data["batch"] == test_user.batch
        assert "password" not in data  # Ensure password not returned
    
    async def test_update_user_profile_success(self, client: AsyncClient, auth_headers):
        """Test updating user profile"""
        update_data = {
            "name": "Updated Name",
            "batch": 2023
        }
        
        response = await client.patch("/users/me", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["batch"] == update_data["batch"]
    
    async def test_get_user_without_auth_fails(self, client: AsyncClient):
        """Test getting user profile without authentication fails"""
        response = await client.get("/users/me")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]


class TestUserAnalytics:
    """Test user analytics endpoints"""
    
    async def test_get_user_analytics_success(self, client: AsyncClient, auth_headers):
        """Test getting user analytics data"""
        response = await client.get("/users/me/analytics", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "current_gpa" in data
        assert "total_credits" in data
        assert "subjects_count" in data
    
    async def test_get_analytics_without_grades(self, client: AsyncClient, auth_headers):
        """Test analytics for user with no grades"""
        response = await client.get("/users/me/analytics", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["current_gpa"] == 0.0
        assert data["total_credits"] == 0
        assert data["subjects_count"] == 0

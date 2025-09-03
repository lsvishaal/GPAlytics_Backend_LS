"""
Test authentication endpoints
Simple integration tests for user registration and login
"""


class TestUserRegistration:
    """Test user registration functionality"""
    
    def test_register_new_user_succeeds(self, test_client, unique_test_user):
        """Test that valid user registration works"""
        # ACT: Register a new user
        response = test_client.post("/auth/register", json=unique_test_user)
        
        # ASSERT: Registration should succeed
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == unique_test_user["name"]
        assert data["regno"] == unique_test_user["regno"]
        assert "password" not in data  # Password should not be returned
        
        # TODO: Add cleanup after we verify this works
    
    def test_register_duplicate_regno_fails(self, test_client, unique_test_user):
        """Test that registering same regno twice fails"""
        # ARRANGE: Register user first time
        test_client.post("/auth/register", json=unique_test_user)
        
        # ACT: Try to register same regno again
        response = test_client.post("/auth/register", json=unique_test_user)
        
        # ASSERT: Should fail with conflict
        assert response.status_code == 409
        
    def test_register_invalid_data_fails(self, test_client):
        """Test that invalid registration data fails"""
        invalid_user = {
            "name": "",  # Empty name
            "regno": "ABC",  # Too short regno
            "password": "123",  # Weak password
            "batch": 1999  # Invalid batch
        }
        
        # ACT: Try to register with invalid data
        response = test_client.post("/auth/register", json=invalid_user)
        
        # ASSERT: Should fail with validation error
        assert response.status_code == 422


class TestUserLogin:
    """Test user login functionality"""
    
    def test_login_valid_credentials_succeeds(self, test_client, unique_test_user):
        """Test that login works with valid credentials"""
        # ARRANGE: Register user first
        test_client.post("/auth/register", json=unique_test_user)
        
        # ACT: Login with credentials
        login_data = {
            "regno": unique_test_user["regno"],
            "password": unique_test_user["password"]
        }
        response = test_client.post("/auth/login", json=login_data)
        
        # ASSERT: Login should succeed and return JWT
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        
    def test_login_wrong_password_fails(self, test_client, unique_test_user):
        """Test that login fails with wrong password"""
        # ARRANGE: Register user first
        test_client.post("/auth/register", json=unique_test_user)
        
        # ACT: Login with wrong password
        login_data = {
            "regno": unique_test_user["regno"],
            "password": "WrongPassword123!"
        }
        response = test_client.post("/auth/login", json=login_data)
        
        # ASSERT: Login should fail
        assert response.status_code == 401
        
    def test_login_nonexistent_user_fails(self, test_client):
        """Test that login fails for non-existent user"""
        # ACT: Try to login with non-existent user
        login_data = {
            "regno": "XX123456789012345",
            "password": "SomePassword123!"
        }
        response = test_client.post("/auth/login", json=login_data)
        
        # ASSERT: Login should fail
        assert response.status_code == 401
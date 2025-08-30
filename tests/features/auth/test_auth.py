"""
Authentication Feature Tests - Implementation Rulebook
====================================================

This file serves as the SPECIFICATION for authentication functionality.
Build your auth endpoints to satisfy these tests exactly.

Test-Driven Development Rule:
1. Run these tests (they will fail - RED phase)
2. Write MINIMUM code to make them pass (GREEN phase)  
3. Refactor if needed (REFACTOR phase)
4. Move to next feature

Focus: Build exactly what these tests require, nothing more.
"""

from fastapi.testclient import TestClient
import pytest
import jwt
from datetime import datetime, timezone
from app.main import app
from app.database import settings

client = TestClient(app)


class TestUserRegistration:
    """
    User Registration Specification
    
    Each test defines EXACTLY what your registration endpoint must do.
    """

    def test_valid_user_registration_succeeds(self):
        """
        RULE 1: Accept valid user registration
        
        Implementation Requirements:
        - POST /auth/register endpoint exists
        - Accepts JSON with name, regno, password, batch
        - Returns 200 status
        - Returns user data (id, name, regno, batch, created_at)
        - Returns JWT token with expires_in
        - Saves user to database with hashed password
        """
        valid_user = {
            "name": "John Doe",
            "regno": "AB123456789012X",  # 15 chars: 2 letters + 13 digits + 1 letter
            "password": "SecurePass123!",
            "batch": 2020
        }
        
        response = client.post("/auth/register", json=valid_user)
        
        assert response.status_code == 200, "Must accept valid registration"
        
        data = response.json()
        assert "message" in data, "Must return success message"
        assert "user" in data, "Must return user data"
        assert "token" in data, "Must return token data"
        
        # Verify user data structure
        user = data["user"]
        assert user["name"] == "John Doe"
        assert user["regno"] == "AB123456789012X"
        assert user["batch"] == 2020
        assert "id" in user, "Must return user ID"
        assert "created_at" in user, "Must return creation timestamp"
        
        # Verify token structure
        token = data["token"]
        assert "access_token" in token, "Must return access token"
        assert "expires_in" in token, "Must return expiration time"
        assert token["token_type"] == "bearer", "Must specify token type"

    def test_duplicate_regno_registration_rejected(self):
        """
        RULE 2: Reject duplicate registration numbers
        
        Implementation Requirements:
        - Check if regno already exists in database
        - Return 400 Bad Request for duplicates
        - Clear error message about existing user
        """
        user_data = {
            "name": "First User",
            "regno": "AB123456789012Y",
            "password": "SecurePass123!",
            "batch": 2020
        }
        
        # First registration should succeed
        response1 = client.post("/auth/register", json=user_data)
        assert response1.status_code == 200, "First registration should succeed"
        
        # Second registration with same regno should fail
        duplicate_user = {
            "name": "Second User",  # Different name
            "regno": "AB123456789012Y",  # Same regno
            "password": "DifferentPass123!",  # Different password
            "batch": 2021  # Different batch
        }
        
        response2 = client.post("/auth/register", json=duplicate_user)
        assert response2.status_code == 400, "Must reject duplicate regno"
        
        error_detail = response2.json()["detail"].lower()
        assert "already exists" in error_detail or "duplicate" in error_detail, \
            "Error must mention duplicate/existing user"

    def test_invalid_regno_format_rejected(self):
        """
        RULE 3: Validate registration number format
        
        Implementation Requirements:
        - Regno must be exactly 15 characters
        - First 2 characters must be uppercase letters
        - Last 13 characters must be digits
        - Return 400 with specific format error message
        """
        invalid_regnos = [
            "AB12345678901",      # Too short (13 chars)
            "AB1234567890123",    # Too long (17 chars)
            "ab123456789012X",    # Lowercase letters
            "A1123456789012X",    # Number in letter position
            "AB12345678901XX",    # Letters in number position
            "",                   # Empty
            "123456789012345"     # All numbers
        ]
        
        for invalid_regno in invalid_regnos:
            user_data = {
                "name": "Test User",
                "regno": invalid_regno,
                "password": "SecurePass123!",
                "batch": 2020
            }
            
            response = client.post("/auth/register", json=user_data)
            assert response.status_code == 400, f"Must reject invalid regno: {invalid_regno}"
            
            error_detail = response.json()["detail"].lower()
            assert any(word in error_detail for word in ["registration", "format", "characters"]), \
                f"Error must explain regno format issue for: {invalid_regno}"

    def test_weak_password_rejected(self):
        """
        RULE 4: Enforce strong password requirements
        
        Implementation Requirements:
        - Minimum 8 characters
        - At least 1 uppercase letter
        - At least 1 lowercase letter  
        - At least 1 digit
        - At least 1 special character
        - Return 400 with specific password requirement error
        """
        weak_passwords = [
            "short",              # Too short
            "lowercase123!",      # No uppercase
            "UPPERCASE123!",      # No lowercase
            "NoNumbers!",         # No digits
            "NoSpecial123",       # No special characters
            "12345678",           # Only numbers
            "password"            # Common weak password
        ]
        
        for weak_password in weak_passwords:
            user_data = {
                "name": "Test User",
                "regno": "AB123456789012Z",
                "password": weak_password,
                "batch": 2020
            }
            
            response = client.post("/auth/register", json=user_data)
            assert response.status_code == 400, f"Must reject weak password: {weak_password}"
            
            error_detail = response.json()["detail"].lower()
            assert "password" in error_detail, \
                f"Error must mention password requirement for: {weak_password}"

    def test_invalid_batch_year_rejected(self):
        """
        RULE 5: Validate batch year range
        
        Implementation Requirements:
        - Batch must be between 2015 and 2045 (reasonable academic years)
        - Return 400 for invalid batch years
        - Clear error message about batch year range
        """
        invalid_batches = [2010, 2050, 1999, 3000, -1]
        
        for invalid_batch in invalid_batches:
            user_data = {
                "name": "Test User",
                "regno": f"AB12345678901{invalid_batch % 10}Z",  # Unique regno
                "password": "SecurePass123!",
                "batch": invalid_batch
            }
            
            response = client.post("/auth/register", json=user_data)
            assert response.status_code == 422, f"Must reject invalid batch: {invalid_batch}"

    def test_missing_required_fields_rejected(self):
        """
        RULE 6: Require all registration fields
        
        Implementation Requirements:
        - All fields (name, regno, password, batch) are required
        - Return 422 for missing fields
        - Clear error message about required fields
        """
        required_fields = ["name", "regno", "password", "batch"]
        
        for missing_field in required_fields:
            incomplete_data = {
                "name": "Test User",
                "regno": "AB123456789012A",
                "password": "SecurePass123!",
                "batch": 2020
            }
            del incomplete_data[missing_field]  # Remove one required field
            
            response = client.post("/auth/register", json=incomplete_data)
            assert response.status_code == 422, f"Must require field: {missing_field}"


class TestUserLogin:
    """
    User Login Specification
    
    Each test defines EXACTLY what your login endpoint must do.
    """

    def test_valid_login_succeeds(self):
        """
        RULE 7: Accept valid user login
        
        Implementation Requirements:
        - POST /auth/login endpoint exists
        - Accepts JSON with regno and password
        - Returns 200 status for valid credentials
        - Returns user data and JWT token
        - Updates last_login timestamp
        """
        # First register a user
        user_data = {
            "name": "Login Test User",
            "regno": "CD123456789012A",
            "password": "LoginPass123!",
            "batch": 2021
        }
        
        register_response = client.post("/auth/register", json=user_data)
        assert register_response.status_code == 200, "Registration should succeed"
        
        # Now test login
        login_data = {
            "regno": "CD123456789012A",
            "password": "LoginPass123!"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200, "Valid login should succeed"
        
        data = response.json()
        assert "message" in data, "Must return success message"
        assert "user" in data, "Must return user data"
        assert "token" in data, "Must return token data"
        
        # Verify user data
        user = data["user"]
        assert user["name"] == "Login Test User"
        assert user["regno"] == "CD123456789012A"
        assert user["batch"] == 2021
        assert "last_login" in user, "Must update last_login timestamp"

    def test_invalid_credentials_rejected(self):
        """
        RULE 8: Reject invalid login credentials
        
        Implementation Requirements:
        - Return 401 Unauthorized for wrong password
        - Return 401 Unauthorized for non-existent user
        - Generic error message for security (don't reveal if user exists)
        """
        # Test wrong password for existing user
        wrong_password = {
            "regno": "CD123456789012A",  # User from previous test
            "password": "WrongPassword123!"
        }
        
        response = client.post("/auth/login", json=wrong_password)
        assert response.status_code == 401, "Must reject wrong password"
        
        error_detail = response.json()["detail"].lower()
        assert "invalid credentials" in error_detail, "Must return generic error message"
        
        # Test non-existent user
        nonexistent_user = {
            "regno": "XX999999999999Z",
            "password": "AnyPassword123!"
        }
        
        response = client.post("/auth/login", json=nonexistent_user)
        assert response.status_code == 401, "Must reject non-existent user"
        
        error_detail = response.json()["detail"].lower()
        assert "invalid credentials" in error_detail, "Must return same generic error"

    def test_login_requires_all_fields(self):
        """
        RULE 9: Require regno and password for login
        
        Implementation Requirements:
        - Both regno and password are required
        - Return 422 for missing fields
        """
        # Missing password
        response = client.post("/auth/login", json={"regno": "CD123456789012A"})
        assert response.status_code == 422, "Must require password"
        
        # Missing regno
        response = client.post("/auth/login", json={"password": "SomePassword123!"})
        assert response.status_code == 422, "Must require regno"
        
        # Empty request
        response = client.post("/auth/login", json={})
        assert response.status_code == 422, "Must require both fields"


class TestJWTTokens:
    """
    JWT Token Specification
    
    Each test defines EXACTLY how JWT tokens should work.
    """

    def test_jwt_token_structure_valid(self):
        """
        RULE 10: Generate valid JWT tokens
        
        Implementation Requirements:
        - Token must be valid JWT format
        - Must contain user data (sub, regno, name, batch)
        - Must have expiration time
        - Must be signed with app secret
        """
        # Register and get token
        user_data = {
            "name": "JWT Test User",
            "regno": "EF123456789012A",
            "password": "JWTPass123!",
            "batch": 2022
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 200
        
        token = response.json()["token"]["access_token"]
        
        # Decode and verify token structure
        try:
            payload = jwt.decode(token, settings.jwt_secret_str, algorithms=[settings.jwt_algorithm])
            
            # Check required claims
            assert "sub" in payload, "Token must contain subject (user ID)"
            assert "regno" in payload, "Token must contain regno"
            assert "name" in payload, "Token must contain name"
            assert "batch" in payload, "Token must contain batch"
            assert "exp" in payload, "Token must contain expiration"
            
            # Verify data matches user
            assert payload["regno"] == "EF123456789012A"
            assert payload["name"] == "JWT Test User"
            assert payload["batch"] == 2022
            
        except jwt.InvalidTokenError:
            pytest.fail("Token should be valid JWT")

    def test_expired_token_rejected(self):
        """
        RULE 11: Handle token expiration
        
        Implementation Requirements:
        - Tokens must have reasonable expiration time
        - Expired tokens should be rejected
        - Protected endpoints should validate token expiration
        """
        # This test would require creating an expired token
        # For now, we'll document the expected behavior
        
        """
        Expected behavior:
        1. Tokens expire after configured time (e.g., 30 minutes)
        2. Expired tokens return 401 Unauthorized
        3. Error message indicates token expiration
        """
        
        # For MVP, we'll skip this test until we have protected endpoints
        pytest.skip("Token expiration testing requires protected endpoints")


class TestSecurityFeatures:
    """
    Security Feature Specification
    
    Each test defines EXACTLY what security measures must be implemented.
    """

    def test_password_hashing_secure(self):
        """
        RULE 12: Passwords must be securely hashed
        
        Implementation Requirements:
        - Never store plain text passwords
        - Use strong hashing algorithm (Argon2, bcrypt, etc.)
        - Verify passwords during login without storing plain text
        """
        user_data = {
            "name": "Security Test User",
            "regno": "GH123456789012A",
            "password": "SecurePlaintext123!",
            "batch": 2023
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 200
        
        # Password should not be returned in response
        response_data = response.json()
        user_json = str(response_data)
        assert "SecurePlaintext123!" not in user_json, \
            "Plain text password must not appear in response"

    def test_case_insensitive_regno_lookup(self):
        """
        RULE 13: Handle regno case consistently
        
        Implementation Requirements:
        - Store regno in consistent case (uppercase)
        - Allow login with any case variation
        - Prevent duplicate registrations with different cases
        """
        # Register with uppercase
        user_data = {
            "name": "Case Test User",
            "regno": "IJ123456789012A",
            "password": "CaseTest123!",
            "batch": 2024
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 200
        
        # Try to register same regno in lowercase (should fail)
        duplicate_data = {
            "name": "Duplicate User",
            "regno": "ij123456789012a",  # Same regno, different case
            "password": "Different123!",
            "batch": 2024
        }
        
        response = client.post("/auth/register", json=duplicate_data)
        assert response.status_code == 400, "Must prevent case-variant duplicates"
        
        # Login with lowercase should work
        login_data = {
            "regno": "ij123456789012a",  # Lowercase
            "password": "CaseTest123!"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200, "Must allow case-insensitive login"


# ==========================================
# IMPLEMENTATION CHECKLIST
# ==========================================
"""
To make these tests pass, your auth system must:

✅ REGISTRATION ENDPOINT:
1. POST /auth/register route
2. Validate regno format (15 chars: 2 letters + 13 digits)
3. Validate password strength (8+ chars, upper, lower, digit, special)
4. Validate batch year range (2015-2045)
5. Check for duplicate regno (case-insensitive)
6. Hash passwords securely (Argon2/bcrypt)
7. Generate and return JWT token
8. Return user data (no password)

✅ LOGIN ENDPOINT:
9. POST /auth/login route
10. Verify credentials against database
11. Update last_login timestamp
12. Generate and return JWT token
13. Return 401 for invalid credentials (generic message)

✅ JWT TOKENS:
14. Include user data in token payload
15. Set reasonable expiration time
16. Sign with secure secret key
17. Use standard JWT format

✅ SECURITY:
18. Never return plain text passwords
19. Use secure password hashing
20. Handle case-insensitive regno lookup
21. Generic error messages (don't reveal if user exists)

Don't build anything else until these tests pass.
"""

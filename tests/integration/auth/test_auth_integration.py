"""
Sprint 1: Authentication Core Tests
=================================

Focus: User registration, login, password validation
Goal: Complete auth foundation before moving to Sprint 2
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_user_registration():
    """User can register with valid credentials"""
    response = client.post("/auth/register", json={
        "name": "Sprint User",
        "regno": "SP1234567890123",
        "password": "SprintPass123!",
        "batch": 2020
    })
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "access_token" in data


def test_user_login():
    """User can login after registration"""
    # Register first
    client.post("/auth/register", json={
        "name": "Login User", 
        "regno": "LG1234567890123",
        "password": "LoginPass123!",
        "batch": 2021
    })
    
    # Then login
    response = client.post("/auth/login", json={
        "regno": "LG1234567890123",
        "password": "LoginPass123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_invalid_registration_data():
    """Registration fails with invalid data"""
    # Invalid regno format
    response = client.post("/auth/register", json={
        "name": "Bad User",
        "regno": "INVALID123",
        "password": "TestPass123!",
        "batch": 2020
    })
    assert response.status_code == 400
    
    # Weak password
    response = client.post("/auth/register", json={
        "name": "Weak User",
        "regno": "WK1234567890123", 
        "password": "weak",
        "batch": 2020
    })
    assert response.status_code == 400


def test_duplicate_registration():
    """Cannot register same regno twice"""
    user_data = {
        "name": "Duplicate User",
        "regno": "DU1234567890123",
        "password": "TestPass123!",
        "batch": 2020
    }
    
    # First registration works
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    
    # Second fails
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 400


def test_wrong_login_credentials():
    """Login fails with wrong credentials"""
    response = client.post("/auth/login", json={
        "regno": "NONEXISTENT123456",
        "password": "WrongPass123!"
    })
    assert response.status_code == 401


# Sprint 1 Complete: 5 focused auth tests
# Next: Sprint 2 - File Upload & Processing

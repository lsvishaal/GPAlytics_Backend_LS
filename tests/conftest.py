"""
Simple test configuration for GPAlytics Backend
Uses Azure SQL - tests create and cleanup their own data
"""
import pytest
import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set testing environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "true"

from app.main import app


@pytest.fixture
def test_client():
    """FastAPI test client"""
    with TestClient(app) as client:
        yield client


@pytest.fixture  
def unique_test_user():
    """Generate unique test user data for each test"""
    import uuid
    import random
    
    # Generate unique test data
    letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))
    digits = ''.join(random.choices('0123456789', k=13))
    
    return {
        "name": f"TEST_USER_{uuid.uuid4().hex[:5].upper()}",
        "regno": letters + digits,
        "password": "TestPass123!",
        "batch": 2021
    }
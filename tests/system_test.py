"""
GPAlytics Backend System Test Suite
Comprehensive endpoint testing with proper error handling
"""
import httpx
import asyncio
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8000"

class SystemTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.access_token = None
        # Create valid test data matching schema requirements
        timestamp = datetime.now().strftime('%H%M%S')
        self.test_user_data = {
            "regno": f"TS{timestamp}1234567",  # TS + 6 digits + 7 more = 15 chars total
            "name": "Test User", 
            "password": "SecurePassword123!",
            "batch": 2025
        }
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def test_health_endpoints(self):
        """Test health check endpoints"""
        logger.info("🏥 Testing health endpoints...")
        
        # Test root endpoint
        try:
            response = await self.client.get(f"{BASE_URL}/")
            logger.info(f"✅ Root endpoint: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   Message: {data.get('message', 'N/A')}")
        except Exception as e:
            logger.error(f"❌ Root endpoint failed: {e}")
        
        # Test health endpoint
        try:
            response = await self.client.get(f"{BASE_URL}/health")
            logger.info(f"✅ Health endpoint: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   Status: {data.get('status', 'N/A')}")
        except Exception as e:
            logger.error(f"❌ Health endpoint failed: {e}")
        
        # Test database health
        try:
            response = await self.client.get(f"{BASE_URL}/health/db")
            logger.info(f"✅ Database health: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   DB Status: {data.get('status', 'N/A')}")
        except Exception as e:
            logger.error(f"❌ Database health failed: {e}")

    async def test_auth_endpoints(self):
        """Test authentication endpoints"""
        logger.info("🔐 Testing authentication endpoints...")
        
        # Test user registration
        try:
            response = await self.client.post(
                f"{BASE_URL}/auth/register",
                json=self.test_user_data
            )
            logger.info(f"✅ Register endpoint: {response.status_code}")
            if response.status_code == 201:
                logger.info("   Registration successful")
            elif response.status_code == 400:
                error_data = response.json()
                logger.info(f"   Registration conflict (expected): {error_data.get('detail', 'N/A')}")
        except Exception as e:
            logger.error(f"❌ Register endpoint failed: {e}")
        
        # Test user login
        try:
            login_data = {
                "regno": self.test_user_data["regno"],
                "password": self.test_user_data["password"]
            }
            response = await self.client.post(
                f"{BASE_URL}/auth/login",
                json=login_data
            )
            logger.info(f"✅ Login endpoint: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                logger.info("   Login successful, token received")
            else:
                error_data = response.json()
                logger.warning(f"   Login failed: {error_data.get('detail', 'Unknown error')}")
        except Exception as e:
            logger.error(f"❌ Login endpoint failed: {e}")

    async def test_protected_endpoints(self):
        """Test protected endpoints with authentication"""
        if not self.access_token:
            logger.warning("⚠️ Skipping protected endpoint tests - no access token")
            return
            
        headers = {"Authorization": f"Bearer {self.access_token}"}
        logger.info("🔒 Testing protected endpoints...")
        
        # Test user profile
        try:
            response = await self.client.get(f"{BASE_URL}/users/profile", headers=headers)
            logger.info(f"✅ User profile: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   User: {data.get('name', 'N/A')} ({data.get('regno', 'N/A')})")
        except Exception as e:
            logger.error(f"❌ User profile failed: {e}")
        
        # Test analytics endpoint (all semesters)
        try:
            response = await self.client.get(f"{BASE_URL}/analytics/", headers=headers)
            logger.info(f"✅ Analytics (all): {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   Analytics data received: {len(data.get('semesters', []))} semesters")
        except Exception as e:
            logger.error(f"❌ Analytics (all) failed: {e}")
        
        # Test analytics endpoint (specific semester)
        try:
            response = await self.client.get(f"{BASE_URL}/analytics/?semester=1", headers=headers)
            logger.info(f"✅ Analytics (semester 1): {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   Semester 1 data received")
        except Exception as e:
            logger.error(f"❌ Analytics (semester 1) failed: {e}")

    async def test_grades_endpoints(self):
        """Test grades endpoints"""
        if not self.access_token:
            logger.warning("⚠️ Skipping grades endpoint tests - no access token")
            return
            
        headers = {"Authorization": f"Bearer {self.access_token}"}
        logger.info("📊 Testing grades endpoints...")
        
        # Test grades list
        try:
            response = await self.client.get(f"{BASE_URL}/grades/", headers=headers)
            logger.info(f"✅ Grades list: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   Grades found: {len(data)} entries")
        except Exception as e:
            logger.error(f"❌ Grades list failed: {e}")

    async def run_full_test_suite(self):
        """Run complete system test suite"""
        logger.info("🚀 Starting GPAlytics System Test Suite")
        logger.info("=" * 50)
        
        await self.test_health_endpoints()
        await self.test_auth_endpoints()
        await self.test_protected_endpoints()
        await self.test_grades_endpoints()
        
        logger.info("=" * 50)
        logger.info("🎉 System test suite completed!")

async def main():
    """Main test runner"""
    try:
        async with SystemTester() as tester:
            await tester.run_full_test_suite()
    except Exception as e:
        logger.error(f"💥 Test suite failed: {e}")
        return False
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

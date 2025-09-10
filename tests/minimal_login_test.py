"""
Minimal Login Test
Test the specific login issue with improved error reporting
"""
import httpx
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8000"

async def test_minimal_login():
    """Test login with known user credentials"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        login_data = {
            "regno": "TS0158271234567",  # Known existing user
            "password": "SecurePassword123!"
        }
        
        logger.info("🔐 Testing login with existing user...")
        try:
            response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
            logger.info(f"Login response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Login successful!")
                logger.info(f"   Message: {data.get('message', 'N/A')}")
                logger.info(f"   User: {data.get('user', {}).get('name', 'N/A')}")
                logger.info(f"   Token received: {bool(data.get('token', {}).get('access_token'))}")
                return True
            else:
                logger.error(f"❌ Login failed: {response.status_code}")
                try:
                    error_data = response.json()
                    logger.error(f"   Error details: {error_data}")
                except:
                    logger.error(f"   Raw response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Login request failed: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_minimal_login())
    print(f"\n{'🎉 SUCCESS' if success else '💥 FAILED'}")

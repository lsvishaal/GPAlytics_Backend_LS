"""
Test Improved Error Handling and Help Endpoints
"""
import httpx
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8000"

async def test_error_handling():
    """Test error handling and new help endpoints"""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test help endpoint
        logger.info("📖 Testing upload help endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/grades/upload-help")
            if response.status_code == 200:
                help_data = response.json()
                logger.info("✅ Help endpoint working")
                logger.info(f"   Supported formats: {help_data['supported_formats']['image_types']}")
                logger.info(f"   Common errors documented: {len(help_data['common_errors'])} types")
            else:
                logger.error(f"Help endpoint failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Help endpoint error: {e}")
        
        # Login for protected endpoints
        login_data = {
            "regno": "TS0158271234567",
            "password": "SecurePassword123!"
        }
        
        logger.info("🔐 Logging in...")
        response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code != 200:
            logger.error("Login failed")
            return
        
        token_data = response.json()
        access_token = token_data.get('token', {}).get('access_token')
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Test grades list endpoint
        logger.info("📋 Testing grades list endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/grades/", headers=headers)
            if response.status_code == 200:
                grades = response.json()
                logger.info(f"✅ Grades endpoint working - found {len(grades)} grades")
            else:
                logger.error(f"Grades endpoint failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Grades endpoint error: {e}")
        
        # Test file validation error
        logger.info("🧪 Testing file validation error handling...")
        try:
            # Create invalid file type
            files = {"file": ("test.txt", b"invalid content", "text/plain")}
            response = await client.post(
                f"{BASE_URL}/grades/process-result-card",
                files=files,
                headers=headers
            )
            logger.info(f"File validation response: {response.status_code}")
            if response.status_code == 400:
                error_data = response.json()
                logger.info(f"✅ File validation error properly handled: {error_data['detail']}")
            
        except Exception as e:
            logger.error(f"File validation test error: {e}")

if __name__ == "__main__":
    asyncio.run(test_error_handling())

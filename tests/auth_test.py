"""
Quick Authentication Test
Test the specific auth flow issue
"""
import httpx
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8000"

async def test_auth_flow():
    """Test detailed authentication flow"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Use a unique regno for testing
        test_data = {
            "regno": "TS0158271234567",  # Exactly 15 chars: TS + 13 digits
            "name": "Auth Test User",
            "password": "SecurePassword123!",
            "batch": 2025
        }
        
        logger.info(f"Testing with regno: {test_data['regno']} (length: {len(test_data['regno'])})")
        
        # Test registration
        logger.info("🔐 Testing registration...")
        try:
            response = await client.post(f"{BASE_URL}/auth/register", json=test_data)
            logger.info(f"Registration response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Registration successful")
                logger.info(f"   User ID: {data.get('user', {}).get('id', 'N/A')}")
                logger.info(f"   Token received: {bool(data.get('token', {}).get('access_token'))}")
            elif response.status_code == 400:
                error_data = response.json()
                logger.info(f"Registration validation error: {error_data}")
                if "already exists" in str(error_data):
                    logger.info("User already exists - proceeding to login test")
            else:
                logger.error(f"Registration failed: {response.text}")
                return
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return
        
        # Test login
        logger.info("🔐 Testing login...")
        login_data = {
            "regno": test_data["regno"],
            "password": test_data["password"]
        }
        
        try:
            response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
            logger.info(f"Login response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Login successful")
                logger.info(f"   User: {data.get('user', {}).get('name', 'N/A')}")
                logger.info(f"   Token: {data.get('token', {}).get('access_token', 'N/A')[:20]}...")
                
                # Test protected endpoint
                token = data.get('token', {}).get('access_token')
                if token:
                    headers = {"Authorization": f"Bearer {token}"}
                    profile_response = await client.get(f"{BASE_URL}/users/profile", headers=headers)
                    logger.info(f"Profile test: {profile_response.status_code}")
                    if profile_response.status_code == 200:
                        profile_data = profile_response.json()
                        logger.info(f"✅ Profile access successful: {profile_data.get('name', 'N/A')}")
                    
            else:
                logger.error(f"Login failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                
        except Exception as e:
            logger.error(f"Login error: {e}")

if __name__ == "__main__":
    asyncio.run(test_auth_flow())

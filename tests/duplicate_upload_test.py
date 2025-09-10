"""
Duplicate Upload Test
Test duplicate grade upload handling to ensure graceful error handling
"""
import httpx
import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8000"

async def test_duplicate_upload():
    """Test duplicate upload handling with a real grade sheet"""
    
    # Use a real grade sheet for testing
    test_image_path = Path("tests/GPAlytics-SEM-Gradesheets/1.jpg")
    
    if not test_image_path.exists():
        logger.error(f"Test image not found: {test_image_path}")
        return False
        
    async with httpx.AsyncClient(timeout=120.0) as client:
        
        # Step 1: Login to get token
        login_data = {
            "regno": "TS0158271234567",
            "password": "SecurePassword123!"
        }
        
        logger.info("🔐 Logging in...")
        try:
            response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
            if response.status_code != 200:
                logger.error(f"Login failed: {response.status_code} - {response.text}")
                return False
                
            token_data = response.json()
            access_token = token_data.get('token', {}).get('access_token')
            if not access_token:
                logger.error("No access token received")
                return False
                
            logger.info("✅ Login successful")
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
        
        # Step 2: First upload (should succeed or fail gracefully)
        headers = {"Authorization": f"Bearer {access_token}"}
        
        logger.info("📤 First upload - testing grade processing...")
        with open(test_image_path, "rb") as f:
            files = {"file": ("grade_sheet.jpg", f.read(), "image/jpeg")}
        
        try:
            response = await client.post(
                f"{BASE_URL}/grades/process-result-card",
                files=files,
                headers=headers
            )
            
            logger.info(f"First upload response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ First upload successful!")
                logger.info(f"   Status: {data.get('status', 'N/A')}")
                logger.info(f"   Message: {data.get('message', 'N/A')}")
                
                if data.get('status') == 'success':
                    grades_added = data.get('data', {}).get('grades_added', 0)
                    logger.info(f"   Grades added: {grades_added}")
            else:
                logger.error(f"❌ First upload failed: {response.status_code}")
                try:
                    error_data = response.json()
                    logger.error(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    logger.error(f"   Raw response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"First upload request failed: {e}")
            return False
        
        # Step 3: Second upload (should detect duplicates)
        logger.info("📤 Second upload - testing duplicate detection...")
        
        with open(test_image_path, "rb") as f:
            files = {"file": ("grade_sheet.jpg", f.read(), "image/jpeg")}
        
        try:
            response = await client.post(
                f"{BASE_URL}/grades/process-result-card",
                files=files,
                headers=headers
            )
            
            logger.info(f"Second upload response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Second upload handled gracefully!")
                logger.info(f"   Status: {data.get('status', 'N/A')}")
                logger.info(f"   Message: {data.get('message', 'N/A')}")
                
                # Check if it detected duplicates
                status = data.get('status')
                if status == 'all_duplicates':
                    logger.info("🔍 ✅ DUPLICATE DETECTION WORKING CORRECTLY!")
                    return True
                elif status == 'success':
                    grades_added = data.get('data', {}).get('grades_added', 0)
                    logger.info(f"   Grades added: {grades_added}")
                    if grades_added == 0:
                        logger.info("🔍 ✅ NO NEW GRADES ADDED - DUPLICATE HANDLING WORKING!")
                        return True
                else:
                    logger.info(f"🔍 Status: {status}")
                    return True
            else:
                logger.error(f"❌ Second upload failed: {response.status_code}")
                try:
                    error_data = response.json()
                    detail = error_data.get('detail', 'Unknown error')
                    logger.error(f"   Error: {detail}")
                    
                    # Check if it's a duplicate error (which is actually good!)
                    if 'duplicate' in detail.lower() or 'already exist' in detail.lower():
                        logger.info("🔍 ✅ DUPLICATE ERROR DETECTED - THIS IS CORRECT BEHAVIOR!")
                        return True
                    else:
                        logger.error(f"❌ Unexpected error: {detail}")
                        return False
                except:
                    logger.error(f"   Raw response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Second upload request failed: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_duplicate_upload())
    print(f"\n{'🎉 DUPLICATE HANDLING TEST PASSED' if success else '💥 DUPLICATE HANDLING TEST FAILED'}")

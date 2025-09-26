"""
Grade Upload Debugging Test
Test grade upload functionality to identify specific issues
"""
import httpx
import asyncio
import logging
from pathlib import Path
import io
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8000"

async def test_grade_upload():
    """Test grade upload functionality with detailed error analysis"""
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
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
        
        # Step 2: Create a test image
        logger.info("🖼️ Creating test grade sheet image...")
        try:
            # Create a simple test image with grade-like content
            img = Image.new('RGB', (800, 600), color='white')
            
            # Convert to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='JPEG', quality=95)
            img_buffer.seek(0)
            img_bytes = img_buffer.getvalue()
            
            logger.info(f"✅ Test image created ({len(img_bytes)} bytes)")
            
        except Exception as e:
            logger.error(f"Failed to create test image: {e}")
            return False
        
        # Step 3: Test grade upload
        headers = {"Authorization": f"Bearer {access_token}"}
        files = {"file": ("test_grades.jpg", img_bytes, "image/jpeg")}
        
        logger.info("📤 Uploading grade sheet...")
        try:
            response = await client.post(
                f"{BASE_URL}/grades/process-result-card",
                files=files,
                headers=headers
            )
            
            logger.info(f"Upload response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Upload successful!")
                logger.info(f"   Status: {data.get('status', 'N/A')}")
                logger.info(f"   Message: {data.get('message', 'N/A')}")
                return True
            else:
                logger.error(f"❌ Upload failed: {response.status_code}")
                try:
                    error_data = response.json()
                    logger.error(f"   Error details: {error_data}")
                    
                    # Analyze specific error types
                    detail = error_data.get('detail', '')
                    if 'rate limit' in detail.lower():
                        logger.error("🔴 GEMINI RATE LIMIT DETECTED")
                    elif 'database' in detail.lower():
                        logger.error("🔴 DATABASE ERROR DETECTED")
                    elif 'ai processing' in detail.lower():
                        logger.error("🔴 AI PROCESSING ERROR DETECTED")
                    elif 'authentication' in detail.lower():
                        logger.error("🔴 AUTHENTICATION ERROR DETECTED")
                    else:
                        logger.error(f"🔴 UNKNOWN ERROR TYPE: {detail}")
                        
                except Exception as parse_error:
                    logger.error(f"   Raw response: {response.text}")
                    logger.error(f"   Parse error: {parse_error}")
                return False
                
        except Exception as e:
            logger.error(f"Upload request failed: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_grade_upload())
    print(f"\n{'🎉 SUCCESS' if success else '💥 FAILED'}")

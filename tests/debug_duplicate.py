"""
Simple Debug Test
Test to identify the exact error location
"""
import httpx
import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8000"

async def debug_upload():
    """Debug upload to see exact error"""
    
    test_image_path = Path("tests/GPAlytics-SEM-Gradesheets/1.jpg")
        
    async with httpx.AsyncClient(timeout=120.0) as client:
        
        # Login
        login_data = {
            "regno": "TS0158271234567",
            "password": "SecurePassword123!"
        }
        
        response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
        token_data = response.json()
        access_token = token_data.get('token', {}).get('access_token')
        
        # Upload with detailed error info
        headers = {"Authorization": f"Bearer {access_token}"}
        
        with open(test_image_path, "rb") as f:
            files = {"file": ("grade_sheet.jpg", f.read(), "image/jpeg")}
        
        try:
            response = await client.post(
                f"{BASE_URL}/grades/process-result-card",
                files=files,
                headers=headers
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                print(f"Raw Response: {response.text}")
                
                try:
                    error_data = response.json()
                    print(f"JSON Error: {error_data}")
                except:
                    print("Could not parse JSON from error response")
            else:
                data = response.json()
                print(f"Success Response: {data}")
                
        except Exception as e:
            print(f"Request Exception: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_upload())

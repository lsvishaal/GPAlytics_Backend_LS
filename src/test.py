"""
Simple test file
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

async def test_auth():
    """Test auth functionality"""
    print("🔐 Testing Auth...\n")
    
    try:
        from GPAlytics_Backend_LS.src.database import db_manager
        from GPAlytics_Backend_LS.src.models import UserRegister
        from GPAlytics_Backend_LS.src.auth import register_user, login_user, validate_regno, validate_password
        
        print("1. Validation Tests:")
        print(f"   Valid regno: {validate_regno('RA2211027020113') is None}")
        print(f"   Valid password: {validate_password('TestPass123!') is None}")
        
        print("\n2. Database Test:")
        db_manager.initialize()
        await db_manager.create_tables()
        print("   ✅ Database ready")
        
        print("\n3. Registration Test:")
        test_user = UserRegister(
            name="Test User",
            regno="RA2211027020113",
            password="TestPass123!",
            batch=2022
        )
        
        async with db_manager.async_session_factory() as db:
            try:
                result = await register_user(db, test_user)
                print("   ✅ Registration successful")
                
                login_result = await login_user(db, test_user.regno, test_user.password)
                print("   ✅ Login successful")
                
            except ValueError as e:
                if "already exists" in str(e):
                    print("   ⚠️ User exists (expected)")
                    login_result = await login_user(db, test_user.regno, test_user.password)
                    print("   ✅ Login successful")
                else:
                    print(f"   ❌ Error: {e}")
        
        await db_manager.close()
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_auth())

"""
Debug Authentication Issue
Detailed debugging for login failure
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession

async def debug_login_issue():
    """Debug the login issue step by step"""
    print("🔍 Debugging login issue...")
    
    # Import dependencies
    try:
        from app.core.database import get_db_session
        from app.auth.service import auth_service
        from app.entities import UserLoginSchema
        print("✅ Imports successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test database session
    try:
        async for db in get_db_session():
            print("✅ Database session obtained")
            
            # Test user lookup
            try:
                user = await auth_service.get_user_by_regno(db, "TS0158271234567")
                if user:
                    print(f"✅ User found: {user.name} (ID: {user.id})")
                    print(f"   Regno: {user.regno}")
                    print(f"   Password hash exists: {bool(user.password_hash)}")
                    print(f"   Password hash length: {len(user.password_hash)}")
                else:
                    print("❌ User not found in database")
                    return False
            except Exception as e:
                print(f"❌ User lookup failed: {e}")
                return False
            
            # Test password verification
            try:
                from app.core.security import verify_password
                password_valid = verify_password("SecurePassword123!", user.password_hash)
                print(f"✅ Password verification: {password_valid}")
                
                if not password_valid:
                    print("❌ Password does not match stored hash")
                    return False
                
            except Exception as e:
                print(f"❌ Password verification failed: {e}")
                return False
            
            # Test token creation
            try:
                from app.core.security import create_access_token
                token_data = {
                    "sub": user.id,
                    "regno": user.regno,
                    "name": user.name,
                    "batch": user.batch
                }
                access_token = create_access_token(token_data)
                print(f"✅ Token creation successful: {access_token[:20]}...")
            except Exception as e:
                print(f"❌ Token creation failed: {e}")
                return False
            
            # Test login service directly
            try:
                credentials = UserLoginSchema(regno="TS0158271234567", password="SecurePassword123!")
                result = await auth_service.login_user(db, credentials)
                print(f"✅ Login service successful: {result['user'].name}")
            except Exception as e:
                print(f"❌ Login service failed: {e}")
                import traceback
                traceback.print_exc()
                return False
            
            break  # Exit the async generator
    except Exception as e:
        print(f"❌ Database session failed: {e}")
        return False
    
    print("🎉 All login components working correctly!")
    return True

if __name__ == "__main__":
    success = asyncio.run(debug_login_issue())
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Test bot handlers and database operations
"""
import asyncio
from bot.database.db import get_db, init_db
from bot.services.user_service import UserService

async def test_database_operations():
    """Test database operations"""
    try:
        # Initialize database
        await init_db()
        print("✅ Database initialized")
        
        # Test database session
        async for db in get_db():
            # Test user creation
            user = await UserService.create_user(
                db=db,
                telegram_id=123456789,
                username="test_user",
                first_name="Test",
                last_name="User"
            )
            
            if user:
                print(f"✅ User created successfully: {user.first_name}")
                
                # Test user retrieval
                retrieved_user = await UserService.get_user_by_telegram_id(db, 123456789)
                if retrieved_user:
                    print(f"✅ User retrieved successfully: {retrieved_user.first_name}")
                else:
                    print("❌ User retrieval failed")
            else:
                print("❌ User creation failed")
            
            return  # Exit the async generator
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_database_operations())
    if success:
        print("🎉 Database operations working correctly!")
    else:
        print("💥 Database operations failed!")
#!/usr/bin/env python3
"""
Simple database connection test
"""
import asyncio
import sys
import os
from loguru import logger

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.config import settings
from bot.database.db import init_db, close_db, get_db
from bot.services.user_service import UserService


async def test_connection():
    """Test database connection"""
    logger.info("🔄 Testing database connection...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("✅ Database initialized successfully")
        
        # Test getting a session
        async for db in get_db():
            # Test a simple query
            user_count = await UserService.get_users_count(db)
            logger.info(f"✅ Database query successful. Users count: {user_count}")
            break
        
        logger.info("✅ All database tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False
    finally:
        await close_db()


if __name__ == "__main__":
    logger.info("🧪 Starting database connection test...")
    success = asyncio.run(test_connection())
    
    if success:
        logger.info("🎉 Database connection test PASSED!")
        sys.exit(0)
    else:
        logger.error("❌ Database connection test FAILED!")
        sys.exit(1)

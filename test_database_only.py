#!/usr/bin/env python3
"""
Test script for database connection only
"""
import asyncio
import sys
from loguru import logger

# Add the bot directory to the path
sys.path.append('bot')

async def test_database():
    """Test database connection"""
    try:
        logger.info("🧪 Testing Database Connection...")
        
        # Import database manager
        from bot.database.db import db_manager
        
        logger.info("✅ Database manager imported successfully")
        
        # Test initialization
        logger.info("🔧 Initializing database...")
        success = await db_manager.initialize()
        
        if success:
            logger.info("✅ Database initialized successfully")
            
            # Test health check
            logger.info("🔍 Testing health check...")
            is_healthy = await db_manager.health_check()
            
            if is_healthy:
                logger.info("✅ Database health check passed")
            else:
                logger.warning("⚠️ Database health check failed")
            
            # Test session creation
            logger.info("📝 Testing connection creation...")
            try:
                connection = await db_manager.get_connection()
                logger.info("✅ Database connection created successfully")
                await db_manager.pool.release(connection)
                logger.info("✅ Database connection released successfully")
            except Exception as e:
                logger.error(f"❌ Connection creation failed: {e}")
                return False
            
        else:
            logger.error("❌ Database initialization failed")
            return False
        
        # Cleanup
        await db_manager.close()
        logger.info("✅ Database connections closed")
        
        logger.info("✅ Database test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False


async def main():
    """Main test function"""
    logger.info("🚀 Starting Database Connection Test...")
    
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    try:
        success = await test_database()
        
        if success:
            logger.info("🎉 Database test PASSED! Connection is working.")
        else:
            logger.error("❌ Database test FAILED! Please check your configuration.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Test interrupted by user")
        sys.exit(1)

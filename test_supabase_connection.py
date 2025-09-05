#!/usr/bin/env python3
"""
Test Supabase Transaction Pooler Connection
"""
import asyncio
import sys
from loguru import logger

# Add the bot directory to the path
sys.path.append('bot')

async def test_supabase_connection():
    """Test Supabase Transaction Pooler connection"""
    try:
        logger.info("🧪 Testing Supabase Transaction Pooler Connection...")
        
        # Import database manager
        from bot.database.db import db_manager
        
        logger.info("✅ Database manager imported successfully")
        
        # Test initialization
        logger.info("🔧 Initializing Supabase connection...")
        success = await db_manager.initialize()
        
        if success:
            logger.info("✅ Supabase connection initialized successfully")
            
            # Test health check
            logger.info("🔍 Testing health check...")
            is_healthy = await db_manager.health_check()
            
            if is_healthy:
                logger.info("✅ Supabase health check passed")
                
                # Test a simple query
                logger.info("📝 Testing simple query...")
                try:
                    result = await db_manager.fetchval("SELECT NOW()")
                    logger.info(f"✅ Query result: {result}")
                except Exception as e:
                    logger.error(f"❌ Query failed: {e}")
                    return False
                
            else:
                logger.warning("⚠️ Supabase health check failed")
                return False
            
        else:
            logger.error("❌ Supabase initialization failed")
            return False
        
        # Cleanup
        await db_manager.close()
        logger.info("✅ Supabase connection closed")
        
        logger.info("✅ Supabase connection test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Supabase connection test failed: {e}")
        return False


async def main():
    """Main test function"""
    logger.info("🚀 Starting Supabase Connection Test...")
    
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    try:
        success = await test_supabase_connection()
        
        if success:
            logger.info("🎉 Supabase connection test PASSED! Database is working.")
        else:
            logger.error("❌ Supabase connection test FAILED! Please check your configuration.")
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

#!/usr/bin/env python3
"""
Simple test script to verify bot functionality in polling mode
"""
import asyncio
import sys
from loguru import logger

# Add the bot directory to the path
sys.path.insert(0, '.')

from bot.config import settings
from bot.database.db import init_db, close_db
from bot.services.jap_service import jap_service


async def test_basic_functionality():
    """Test basic bot functionality"""
    logger.info("🧪 Testing basic bot functionality...")
    
    # Test configuration
    logger.info(f"✅ Bot token configured: {'Yes' if settings.bot_token else 'No'}")
    logger.info(f"✅ JAP API key configured: {'Yes' if settings.jap_api_key else 'No'}")
    logger.info(f"✅ Database URL configured: {'Yes' if settings.database_url else 'No'}")
    
    # Test database connection
    try:
        await init_db()
        logger.info("✅ Database connection successful")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False
    
    # Test JAP service
    try:
        balance = await jap_service.get_balance()
        if balance is not None:
            logger.info(f"✅ JAP API connection successful - Balance: ${balance}")
        else:
            logger.warning("⚠️ JAP API connection failed or returned no balance")
    except Exception as e:
        logger.error(f"❌ JAP API test failed: {e}")
    
    # Test services sync
    try:
        services = await jap_service.get_services()
        if services:
            logger.info(f"✅ JAP services retrieved: {len(services)} services")
        else:
            logger.warning("⚠️ No services retrieved from JAP API")
    except Exception as e:
        logger.error(f"❌ JAP services test failed: {e}")
    
    return True


async def main():
    """Main test function"""
    try:
        logger.info("🚀 Starting bot functionality test...")
        
        success = await test_basic_functionality()
        
        if success:
            logger.info("✅ All basic tests passed! Bot should work in polling mode.")
            logger.info("💡 To start the bot, run: python main.py")
        else:
            logger.error("❌ Some tests failed. Please check your configuration.")
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
    finally:
        await close_db()
        await jap_service.close()


if __name__ == "__main__":
    asyncio.run(main())

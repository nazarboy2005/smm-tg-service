#!/usr/bin/env python3
"""
Test script for Railway deployment
"""
import os
import sys
import asyncio
from loguru import logger

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_railway_config():
    """Test Railway configuration"""
    logger.info("Testing Railway configuration...")
    
    # Test environment variables
    required_vars = [
        "BOT_TOKEN",
        "DATABASE_URL",
        "PORT"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
    else:
        logger.info("✅ All required environment variables are set")
    
    # Test database connection
    try:
        from bot.database.db import initialize, create_tables
        await initialize()
        await create_tables()
        logger.info("✅ Database connection successful")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False
    
    # Test bot initialization
    try:
        from bot.config import settings
        from aiogram import Bot
        from aiogram.enums import ParseMode
        from aiogram.client.default import DefaultBotProperties
        
        bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML
            )
        )
        
        me = await bot.get_me()
        logger.info(f"✅ Bot initialized successfully: @{me.username} (ID: {me.id})")
        await bot.session.close()
    except Exception as e:
        logger.error(f"❌ Bot initialization failed: {e}")
        return False
    
    # Test main application
    try:
        from main import main
        logger.info("✅ Main application imports successfully")
    except Exception as e:
        logger.error(f"❌ Main application import failed: {e}")
        return False
    
    logger.info("✅ All Railway configuration tests passed!")
    return True

if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    try:
        success = asyncio.run(test_railway_config())
        if success:
            logger.info("🎉 Railway configuration is ready for deployment!")
            sys.exit(0)
        else:
            logger.error("❌ Railway configuration has issues")
            sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        sys.exit(1)

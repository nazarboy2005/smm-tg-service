#!/usr/bin/env python3
"""
Test simple bot with basic handlers
"""
import asyncio
import sys
from loguru import logger

# Add the bot directory to the path
sys.path.insert(0, '.')

from bot.config import settings
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from bot.handlers.simple_handlers import router

async def test_simple_bot():
    """Test simple bot functionality"""
    try:
        logger.info("🤖 Testing simple bot functionality...")
        
        # Create bot instance
        bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML
            )
        )
        
        # Test bot connection
        me = await bot.get_me()
        logger.info(f"✅ Bot connected: @{me.username} (ID: {me.id})")
        
        # Create dispatcher
        dp = Dispatcher()
        
        # Register simple handlers
        dp.include_router(router)
        
        logger.info("✅ Simple handlers registered")
        logger.info("🤖 Starting bot in polling mode...")
        logger.info("💡 Send /start, /ping, /test, or any message to your bot!")
        logger.info("🛑 Press Ctrl+C to stop the bot")
        
        # Start polling
        try:
            await dp.start_polling(bot, drop_pending_updates=True)
        except KeyboardInterrupt:
            logger.info("👋 Bot stopped by user")
        except Exception as e:
            logger.error(f"❌ Polling error: {e}")
        
        await bot.session.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Bot test failed: {e}")
        return False

async def main():
    """Main test function"""
    try:
        logger.info("🚀 Starting simple bot test...")
        
        success = await test_simple_bot()
        
        if success:
            logger.info("✅ Bot is working correctly!")
        else:
            logger.error("❌ Bot is not responding properly")
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Simple bot test without database dependencies
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

async def simple_bot_test():
    """Test bot without database"""
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
        
        # Add a simple test handler
        @dp.message()
        async def echo_handler(message):
            await message.answer(f"🧪 Test response: {message.text}")
        
        logger.info("✅ Bot handlers registered")
        logger.info("🤖 Starting bot in polling mode for 30 seconds...")
        logger.info("💡 Send a message to your bot to test it!")
        
        # Start polling for 30 seconds
        try:
            await dp.start_polling(bot, timeout=30)
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
        
        success = await simple_bot_test()
        
        if success:
            logger.info("✅ Bot is working correctly!")
            logger.info("💡 Try sending a message to your bot in Telegram")
        else:
            logger.error("❌ Bot is not responding properly")
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Test script to check if bot is responding
"""
import asyncio
import sys
from loguru import logger

# Add the bot directory to the path
sys.path.insert(0, '.')

from bot.config import settings
from aiogram import Bot

async def test_bot_response():
    """Test if bot is responding"""
    try:
        logger.info("🤖 Testing bot response...")
        
        # Create bot instance
        bot = Bot(token=settings.bot_token)
        
        # Get bot info
        me = await bot.get_me()
        logger.info(f"✅ Bot info: @{me.username} (ID: {me.id})")
        
        # Test sending a message to yourself (if you're an admin)
        if settings.admin_ids:
            admin_id = settings.admin_ids[0]
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text="🧪 Bot test message - If you see this, the bot is working!"
                )
                logger.info(f"✅ Test message sent to admin {admin_id}")
            except Exception as e:
                logger.warning(f"⚠️ Could not send test message: {e}")
        
        await bot.session.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Bot test failed: {e}")
        return False

async def main():
    """Main test function"""
    try:
        logger.info("🚀 Starting bot response test...")
        
        success = await test_bot_response()
        
        if success:
            logger.info("✅ Bot is working correctly!")
            logger.info("💡 Try sending /start to your bot in Telegram")
        else:
            logger.error("❌ Bot is not responding properly")
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

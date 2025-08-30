#!/usr/bin/env python3
"""
Test bot functionality
"""
import asyncio
from loguru import logger
from aiogram import Bot
from bot.config import settings


async def test_bot():
    """Test basic bot functionality"""
    try:
        logger.info("🧪 Testing bot functionality...")
        
        # Initialize bot
        bot = Bot(token=settings.bot_token)
        
        # Get bot info
        me = await bot.get_me()
        logger.success(f"✅ Bot is working: @{me.username} (ID: {me.id})")
        
        # Check webhook status
        webhook_info = await bot.get_webhook_info()
        logger.info(f"📡 Webhook URL: {webhook_info.url}")
        logger.info(f"📊 Pending updates: {webhook_info.pending_update_count}")
        
        if webhook_info.last_error_date:
            logger.warning(f"⚠️ Last webhook error: {webhook_info.last_error_message}")
        else:
            logger.success("✅ No webhook errors")
        
        # Test database connection
        try:
            from bot.database.db import init_db
            await init_db()
            logger.success("✅ Database connection working")
        except Exception as e:
            logger.error(f"❌ Database error: {e}")
        
        await bot.session.close()
        logger.success("🎉 Bot test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Bot test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_bot())
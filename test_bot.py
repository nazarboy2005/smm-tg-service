#!/usr/bin/env python3
"""
Simple bot test script to verify token and basic functionality
Run this to test if the bot token works and can receive messages
"""
import asyncio
import sys
from loguru import logger
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings


# Simple message handler for testing
async def start_handler(message: types.Message):
    """Handle /start command"""
    logger.info(f"Received /start from user {message.from_user.id}: @{message.from_user.username}")
    
    await message.answer(
        "🚀 <b>Elite JAP Bot is working!</b>\n\n"
        "✅ Bot token is valid\n"
        "✅ Handlers are responding\n"
        "✅ Connection established\n\n"
        "Your bot is now ready for production!",
        parse_mode=ParseMode.HTML
    )


async def any_message_handler(message: types.Message):
    """Handle any message for testing"""
    logger.info(f"Received message from user {message.from_user.id}: {message.text}")
    
    await message.answer(
        f"✅ Bot received your message: <code>{message.text}</code>\n\n"
        f"👤 User ID: <code>{message.from_user.id}</code>\n"
        f"📱 Username: @{message.from_user.username}\n"
        f"📅 Message ID: <code>{message.message_id}</code>",
        parse_mode=ParseMode.HTML
    )


async def test_bot():
    """Test bot functionality"""
    try:
        logger.info("🧪 Starting bot test...")
        logger.info(f"🔑 Bot token: {settings.bot_token[:10]}...")
        logger.info(f"👤 Bot username: @{settings.bot_username}")
        
        # Initialize bot
        bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # Test bot token validity
        logger.info("🔍 Testing bot token...")
        me = await bot.get_me()
        logger.success(f"✅ Bot token is valid!")
        logger.info(f"🤖 Bot info: @{me.username} ({me.first_name})")
        logger.info(f"🆔 Bot ID: {me.id}")
        
        # Check webhook status
        logger.info("🌐 Checking webhook status...")
        webhook_info = await bot.get_webhook_info()
        logger.info(f"📡 Webhook URL: {webhook_info.url}")
        logger.info(f"📊 Pending updates: {webhook_info.pending_update_count}")
        
        if webhook_info.url:
            logger.info("🔗 Bot is in WEBHOOK mode")
            if webhook_info.last_error_date:
                logger.warning(f"⚠️ Last webhook error: {webhook_info.last_error_message}")
        else:
            logger.info("📡 Bot is in POLLING mode (no webhook set)")
        
        # Initialize dispatcher for testing
        dp = Dispatcher()
        
        # Register test handlers
        dp.message.register(start_handler, CommandStart())
        dp.message.register(any_message_handler)
        
        logger.success("✅ Bot test completed successfully!")
        logger.info("💬 Send a message to @nimadirishqiladiganbot to test")
        
        # If in polling mode, start polling for testing
        if not webhook_info.url:
            logger.info("🔄 Starting polling mode for testing...")
            logger.info("Press Ctrl+C to stop")
            await dp.start_polling(bot, drop_pending_updates=True)
        else:
            logger.info("🌐 Bot is in webhook mode - test by sending messages via Telegram")
            
        await bot.session.close()
        
    except Exception as e:
        logger.error(f"❌ Bot test failed: {e}")
        logger.error("🔍 Possible issues:")
        logger.error("   1. Invalid bot token")
        logger.error("   2. Network connectivity issues")
        logger.error("   3. Bot blocked or restricted")
        logger.error("   4. Telegram API issues")
        sys.exit(1)


if __name__ == "__main__":
    logger.info("🚀 Elite JAP Bot - Test Script")
    logger.info("=" * 50)
    
    try:
        asyncio.run(test_bot())
    except KeyboardInterrupt:
        logger.info("🛑 Test stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)
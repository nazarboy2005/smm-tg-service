#!/usr/bin/env python3
"""
Run bot in polling mode for local testing
This bypasses webhook issues and tests bot functionality directly
"""
import asyncio
import sys
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.database.db import initialize, create_tables
from bot.handlers import simple_handlers, user_handlers, admin_handlers, admin_settings_handlers, support_handlers
from bot.middleware import SecurityMiddleware, LoggingMiddleware, LanguageMiddleware


async def main():
    """Run bot in polling mode"""
    try:
        # Configure logging
        logger.remove()
        logger.add(
            sys.stdout,
            level="INFO",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        
        logger.info("🚀 Starting bot in POLLING mode for local testing...")
        
        # Initialize database
        try:
            await initialize()
            await create_tables()
            logger.info("✅ Database initialized")
        except Exception as e:
            logger.warning(f"⚠️ Database initialization failed: {e}")
            logger.info("Continuing without database...")
        
        # Initialize bot
        bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        me = await bot.get_me()
        logger.info(f"✅ Bot initialized: @{me.username} (ID: {me.id})")
        
        # Initialize dispatcher
        dp = Dispatcher()
        
        # Register middleware
        dp.message.middleware(SecurityMiddleware())
        dp.callback_query.middleware(SecurityMiddleware())
        dp.message.middleware(LanguageMiddleware())
        dp.callback_query.middleware(LanguageMiddleware())
        dp.message.middleware(LoggingMiddleware())
        dp.callback_query.middleware(LoggingMiddleware())
        
        # Register handlers - simple handlers first for testing
        try:
            dp.include_router(simple_handlers.router)
            logger.info("✅ Simple handlers registered")
        except Exception as e:
            logger.error(f"❌ Failed to register simple handlers: {e}")
        
        try:
            dp.include_router(user_handlers.router)
            logger.info("✅ User handlers registered")
        except Exception as e:
            logger.error(f"❌ Failed to register user handlers: {e}")
            
        try:
            dp.include_router(admin_handlers.router)
            logger.info("✅ Admin handlers registered")
        except Exception as e:
            logger.error(f"❌ Failed to register admin handlers: {e}")
            
        try:
            dp.include_router(admin_settings_handlers.router)
            logger.info("✅ Admin settings handlers registered")
        except Exception as e:
            logger.error(f"❌ Failed to register admin settings handlers: {e}")
            
        try:
            dp.include_router(support_handlers.router)
            logger.info("✅ Support handlers registered")
        except Exception as e:
            logger.error(f"❌ Failed to register support handlers: {e}")
        
        # Delete webhook to switch to polling
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("✅ Webhook deleted, switching to polling mode")
        except Exception as e:
            logger.warning(f"⚠️ Failed to delete webhook: {e}")
        
        # Start polling
        logger.success("🎉 Bot is now running in POLLING mode!")
        logger.info("📱 Send a message to your bot to test it!")
        logger.info("🛑 Press Ctrl+C to stop the bot")
        
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        if 'bot' in locals():
            await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
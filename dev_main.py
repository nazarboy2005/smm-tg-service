"""
Development main bot application - Forces polling mode
"""
import asyncio
import sys
import threading
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.database.db import init_db, close_db
from bot.handlers import user_handlers, admin_handlers, admin_settings_handlers, support_handlers
from bot.services.jap_service import jap_service
from bot.services.payment_service import payment_service
from bot.middleware import SecurityMiddleware, LoggingMiddleware, LanguageMiddleware
from bot.web.server import start_web_server


async def main():
    """Main bot function for development - forces polling mode"""
    try:
        # Configure logging
        logger.remove()
        logger.add(
            sys.stdout,
            level="INFO",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        
        logger.info("Starting SMM Bot in DEVELOPMENT MODE (Polling)...")
        
        # Check if we have basic configuration
        if not hasattr(settings, 'bot_token') or not settings.bot_token:
            logger.error("BOT_TOKEN not configured! Please set your bot token.")
            logger.info("You can either:")
            logger.info("1. Create a .env file with BOT_TOKEN=your_token")
            logger.info("2. Set the BOT_TOKEN environment variable")
            logger.info("3. Run simple_bot.py for a basic working version")
            raise ValueError("BOT_TOKEN is required")
        
        # Initialize database with better error handling
        try:
            await init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            logger.warning("Running in basic mode without database - some features will be limited")
            # Continue without database for basic functionality
        
        # Initialize bot with proper error handling
        try:
            bot = Bot(
                token=settings.bot_token,
                default=DefaultBotProperties(
                    parse_mode=ParseMode.HTML
                )
            )
            
            # Test bot token validity
            me = await bot.get_me()
            logger.info(f"Bot initialized successfully: @{me.username} (ID: {me.id})")
            logger.info(f"Bot username from settings: @{settings.bot_username}")
            
            # Update bot username in settings if different
            if hasattr(settings, 'bot_username') and settings.bot_username != me.username:
                logger.warning(f"Bot username mismatch! Settings: @{settings.bot_username}, Actual: @{me.username}")
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            logger.error("Please check your bot token and network connection")
            raise
        
        # Initialize dispatcher
        dp = Dispatcher()
        
        # Register middleware
        dp.message.middleware(SecurityMiddleware())
        dp.callback_query.middleware(SecurityMiddleware())
        dp.message.middleware(LanguageMiddleware())
        dp.callback_query.middleware(LanguageMiddleware())
        dp.message.middleware(LoggingMiddleware())
        dp.callback_query.middleware(LoggingMiddleware())
        
        # Register handlers
        dp.include_router(user_handlers.router)
        dp.include_router(admin_handlers.router)
        dp.include_router(admin_settings_handlers.router)
        dp.include_router(support_handlers.router)
        
        logger.info("Bot handlers registered")
        
        # Initialize default settings
        try:
            from bot.database.db import get_db_session
            from bot.services.settings_service import SettingsService
            
            db = await get_db_session()
            try:
                await SettingsService.initialize_default_settings(db)
                logger.info("Default settings initialized")
            finally:
                await db.close()
        except Exception as e:
            logger.warning(f"Failed to initialize default settings: {e}")
        
        # Create demo services
        try:
            from bot.database.db import get_db_session
            from bot.services.service_service import ServiceService
            
            db = await get_db_session()
            try:
                await ServiceService.create_demo_categories_and_services(db)
                logger.info("Demo services created successfully")
            finally:
                await db.close()
        except Exception as e:
            logger.warning(f"Failed to create demo services: {e}")
        
        # Start web server in a separate thread (optional for development)
        if getattr(settings, 'enable_web_server', True):
            logger.info("Starting web server...")
            
            # Set bot and dispatcher for webhook handling
            from bot.web.server import set_bot_and_dispatcher
            set_bot_and_dispatcher(bot, dp)
            
            # Give a small delay to ensure bot is fully initialized
            await asyncio.sleep(1)
            
            web_thread = threading.Thread(target=start_web_server)
            web_thread.daemon = True
            web_thread.start()
            logger.info("Web server started on port 8000")
        
        # Force polling mode for development
        logger.info("=== DEVELOPMENT MODE ===")
        logger.info("Running in POLLING mode (no webhook)")
        
        # Always delete webhook for polling mode
        logger.info("Deleting any existing webhook for polling mode...")
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("Webhook deleted successfully")
        except Exception as e:
            logger.warning(f"Error deleting webhook: {e}")
        
        logger.info("Bot is now active and listening for messages!")
        logger.info("Press Ctrl+C to stop the bot")
        logger.info("========================")
        
        try:
            await dp.start_polling(bot, drop_pending_updates=True)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Error in polling: {e}")
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise
    finally:
        # Cleanup
        try:
            await jap_service.close()
            await payment_service.close_all_providers()
            await close_db()
            logger.info("Bot shutdown completed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

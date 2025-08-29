"""
Main bot application
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
    """Main bot function"""
    try:
        # Configure logging
        logger.remove()
        logger.add(
            sys.stdout,
            level=settings.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        logger.add(
            settings.log_file,
            level=settings.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="30 days"
        )
        
        logger.info("Starting SMM Bot...")
        
        # Initialize database with better error handling
        try:
            await init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            logger.error("Please check your database configuration and connection")
            raise
        
        # Initialize bot
        bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML
            )
        )
        
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
            from bot.database.db import get_db
            from bot.services.settings_service import SettingsService
            
            async for db in get_db():
                await SettingsService.initialize_default_settings(db)
                break
            
            logger.info("Default settings initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize default settings: {e}")
        
        # Sync services from JAP API on startup
        try:
            from bot.database.db import get_db
            from bot.services.service_service import ServiceService
            
            async for db in get_db():
                await ServiceService.sync_services_from_jap(db)
                break
            
            logger.info("Services synced from JAP API")
        except Exception as e:
            logger.warning(f"Failed to sync services from JAP API: {e}")
        
        # Start web server in a separate thread - always enabled for better UX
        logger.info("Starting web server...")
        web_thread = threading.Thread(target=start_web_server)
        web_thread.daemon = True
        web_thread.start()
        logger.info("Web server started on port 8000")
        
        # Start polling
        logger.info("Bot started successfully")
        await dp.start_polling(bot)
        
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

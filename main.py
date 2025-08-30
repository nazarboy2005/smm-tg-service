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
            level="INFO",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        
        logger.info("Starting SMM Bot...")
        
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
        
        # Sync services from JAP API on startup (non-critical)
        try:
            from bot.database.db import get_db_session
            from bot.services.service_service import ServiceService
            
            db = await get_db_session()
            try:
                success = await ServiceService.sync_services_from_jap(db)
                if success:
                    logger.info("Services synced from JAP API successfully")
                else:
                    logger.warning("JAP API sync failed, using demo services instead")
                    # Create demo services if JAP API fails
                    await ServiceService.create_demo_categories_and_services(db)
                    logger.info("Demo services created as fallback")
            finally:
                await db.close()
            
        except Exception as e:
            logger.warning(f"Failed to sync services from JAP API, creating demo services: {e}")
            try:
                db = await get_db_session()
                try:
                    await ServiceService.create_demo_categories_and_services(db)
                    logger.info("Demo services created as fallback")
                finally:
                    await db.close()
            except Exception as demo_error:
                logger.error(f"Failed to create demo services: {demo_error}")
        
        # Start web server in a separate thread - always enabled for better UX
        logger.info("Starting web server...")
        
        # Set bot and dispatcher for webhook handling
        from bot.web.server import set_bot_and_dispatcher
        set_bot_and_dispatcher(bot, dp)
        
        web_thread = threading.Thread(target=start_web_server)
        web_thread.daemon = True
        web_thread.start()
        logger.info("Web server started on port 8000")
        
        # Check webhook configuration
        webhook_url = getattr(settings, 'webhook_url', None)
        use_webhook = getattr(settings, 'use_webhook', False)
        
        if use_webhook and webhook_url:
            # Webhook mode
            logger.info("Running in webhook mode...")
            try:
                await bot.delete_webhook(drop_pending_updates=True)
                await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"Error clearing webhook: {e}")
            
            webhook_secret = getattr(settings, 'webhook_secret', None)
            logger.info(f"Setting up webhook at: {webhook_url}/webhook")
            
            try:
                await bot.set_webhook(
                    url=f"{webhook_url}/webhook",
                    drop_pending_updates=True,
                    secret_token=webhook_secret
                )
                
                webhook_info = await bot.get_webhook_info()
                logger.info(f"Webhook set successfully: {webhook_info.url}")
                logger.info("Bot is now running in webhook mode.")
                
                # Keep the main thread alive
                import signal
                def signal_handler(signum, frame):
                    logger.info("Received shutdown signal")
                    raise KeyboardInterrupt
                
                signal.signal(signal.SIGINT, signal_handler)
                signal.signal(signal.SIGTERM, signal_handler)
                
                try:
                    while True:
                        await asyncio.sleep(10)
                except KeyboardInterrupt:
                    logger.info("Shutting down webhook bot...")
                    await bot.delete_webhook(drop_pending_updates=True)
            except Exception as e:
                logger.error(f"Failed to set webhook: {e}")
                logger.info("Falling back to polling mode...")
                await dp.start_polling(bot)
        else:
            # Polling mode (default for development)
            logger.info("Running in polling mode...")
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

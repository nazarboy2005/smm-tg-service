#!/usr/bin/env python3
"""
Main bot application - Updated for JAP API compatibility
"""
import asyncio
import sys
import signal
import os
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.handlers import user_handlers, admin_handlers, admin_settings_handlers, support_handlers
from bot.middleware import SecurityMiddleware, LoggingMiddleware, LanguageMiddleware


# Global variables for cleanup
bot = None
dp = None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal")
    if bot and dp:
        asyncio.create_task(shutdown())

async def shutdown():
    """Graceful shutdown"""
    try:
        logger.info("Shutting down bot...")
        
        # Close payment providers
        try:
            from bot.services.payment_service import payment_service
            await payment_service.close_all_providers()
            logger.info("Closed all payment provider connections")
        except Exception as e:
            logger.warning(f"Error closing payment providers: {e}")
        
        # Close database
        try:
            from bot.database.db import close
            await close()
            logger.info("Database connection closed")
        except Exception as e:
            logger.warning(f"Error closing database: {e}")
        
        # Close bot session
        if bot:
            await bot.session.close()
        
        logger.info("Bot shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

async def main():
    """Main bot function"""
    global bot, dp
    
    try:
        # Configure logging
        logger.remove()
        logger.add(
            sys.stdout,
            level="INFO",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        
        logger.info("Starting SMM Bot with JAP API integration...")
        
        # Initialize payment providers
        try:
            from bot.services.payment_service import payment_service
            # Payment providers are automatically initialized when the service is created
            logger.info("Payment providers initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize payment providers: {e}")
        
        # Initialize database
        try:
            from bot.database.db import initialize, create_tables
            await initialize()
            await create_tables()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return
        
        # Initialize bot
        try:
            bot = Bot(
                token=settings.bot_token,
                default=DefaultBotProperties(
                    parse_mode=ParseMode.HTML
                )
            )
            
            me = await bot.get_me()
            logger.info(f"Bot initialized successfully: @{me.username} (ID: {me.id})")
            logger.info(f"Bot username from settings: @{settings.bot_username}")
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            return
        
        # Initialize dispatcher
        dp = Dispatcher()
        
        # Register middleware
        dp.message.middleware(SecurityMiddleware())
        dp.callback_query.middleware(SecurityMiddleware())
        dp.message.middleware(LanguageMiddleware())
        dp.callback_query.middleware(LanguageMiddleware())
        dp.message.middleware(LoggingMiddleware())
        dp.callback_query.middleware(LoggingMiddleware())
        
        # Register main handlers first (higher priority)
        try:
            dp.include_router(user_handlers.router)
            logger.info("User handlers registered")
        except Exception as e:
            logger.error(f"Failed to register user handlers: {e}")
            
        try:
            dp.include_router(admin_handlers.router)
            logger.info("Admin handlers registered")
        except Exception as e:
            logger.error(f"Failed to register admin handlers: {e}")
            
        try:
            dp.include_router(admin_settings_handlers.router)
            logger.info("Admin settings handlers registered")
        except Exception as e:
            logger.error(f"Failed to register admin settings handlers: {e}")
            
        try:
            dp.include_router(support_handlers.router)
            logger.info("Support handlers registered")
        except Exception as e:
            logger.error(f"Failed to register support handlers: {e}")
        

        
        logger.info("Bot handlers registered")
        
        # Initialize default settings
        try:
            from bot.services.settings_service import SettingsService
            from bot.database.db import get_db
            async for db in get_db():
                await SettingsService.initialize_default_settings(db)
                break
            logger.info("Default settings initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize default settings: {e}")
        
        # Test JAP API connection (optional)
        try:
            from bot.services.service_service import ServiceService
            logger.info("Testing JAP API connection...")
            
            # Test balance fetch
            balance_info = await ServiceService.get_jap_balance()
            if balance_info:
                balance = balance_info.get("balance", "0")
                currency = balance_info.get("currency", "USD")
                logger.info(f"✅ JAP API connected - Balance: {balance} {currency}")
            else:
                logger.warning("⚠️ JAP API not configured or connection failed (this is normal)")
            
            # Test service fetch
            services = await ServiceService.get_services_from_jap()
            if services:
                logger.info(f"✅ JAP API services available - {len(services)} services found")
            else:
                logger.warning("⚠️ No services available from JAP API (this is normal if not configured)")
                
        except Exception as e:
            logger.warning(f"JAP API test failed (this is normal if not configured): {e}")
        
        # Set bot and dispatcher for webhook handling (for web interface)
        from bot.web.server import set_bot_and_dispatcher
        set_bot_and_dispatcher(bot, dp)
        
        # Run in polling mode
        logger.info("Running in polling mode...")
        
        # Delete any existing webhook to ensure polling works
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("Webhook deleted, starting polling...")
        except Exception as e:
            logger.warning(f"Failed to delete webhook: {e}")
        
        # Start polling
        logger.info("🤖 Bot is ready to receive messages via polling!")
        await dp.start_polling(bot, skip_updates=True)
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise
    finally:
        await shutdown()

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

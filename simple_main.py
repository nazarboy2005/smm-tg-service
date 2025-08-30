"""
Simplified main bot application without database issues
"""
import asyncio
import sys
import threading
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.handlers import user_handlers, admin_handlers, admin_settings_handlers, support_handlers
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
        
        logger.info("Starting SMM Bot (Simplified)...")
        
        # Check if we have basic configuration
        if not hasattr(settings, 'bot_token') or not settings.bot_token:
            logger.error("BOT_TOKEN not configured! Please set your bot token.")
            raise ValueError("BOT_TOKEN is required")
        
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
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
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
        
        # Start web server in a separate thread
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
        
        # Run in polling mode (simplified)
        logger.info("Running in polling mode...")
        logger.info("Bot is now active and listening for messages!")
        logger.info("Press Ctrl+C to stop the bot")
        
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

"""
Web server entry point for Railway deployment
This file starts the FastAPI web server and initializes the bot for webhook handling
"""
import os
import asyncio
import signal
import sys
from loguru import logger

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.config import settings
from bot.database.db import initialize, create_tables
from bot.services.settings_service import SettingsService
from bot.services.payment_service import payment_service
from bot.web.server import app, set_bot_and_dispatcher
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Global variables
bot = None
dp = None

async def initialize_bot():
    """Initialize bot and dispatcher for webhook handling"""
    global bot, dp
    
    try:
        # Initialize database
        await initialize()
        await create_tables()
        logger.info("Database initialized successfully")
        
        # Initialize default settings
        from bot.database.db import get_db
        async for db in get_db():
            await SettingsService.initialize_default_settings(db)
            break
        logger.info("Default settings initialized")
        
        # Initialize bot
        bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML
            )
        )
        
        me = await bot.get_me()
        logger.info(f"Bot initialized successfully: @{me.username} (ID: {me.id})")
        
        # Initialize dispatcher
        dp = Dispatcher()
        
        # Register middleware
        from bot.middleware import SecurityMiddleware, LoggingMiddleware, LanguageMiddleware
        dp.message.middleware(SecurityMiddleware())
        dp.callback_query.middleware(SecurityMiddleware())
        dp.message.middleware(LanguageMiddleware())
        dp.callback_query.middleware(LanguageMiddleware())
        dp.message.middleware(LoggingMiddleware())
        dp.callback_query.middleware(LoggingMiddleware())
        
        # Register handlers
        from bot.handlers import user_handlers, admin_handlers, admin_settings_handlers, support_handlers
        dp.include_router(user_handlers.router)
        dp.include_router(admin_handlers.router)
        dp.include_router(admin_settings_handlers.router)
        dp.include_router(support_handlers.router)
        
        logger.info("Bot handlers registered")
        
        # Set bot and dispatcher for webhook handling
        set_bot_and_dispatcher(bot, dp)
        
        # Set up webhook
        # Get webhook URL from environment or use Railway's domain
        webhook_base = os.environ.get("WEBHOOK_BASE_URL")
        if not webhook_base:
            # Try to get Railway's domain from environment
            railway_domain = os.environ.get("RAILWAY_STATIC_URL")
            if railway_domain:
                webhook_base = f"https://{railway_domain}"
            else:
                # Fallback to default
                webhook_base = "https://smm-tg-service-production.up.railway.app"
        
        webhook_url = f"{webhook_base}/webhook"
        logger.info(f"Setting up webhook at: {webhook_url}")
        
        try:
            await bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query"]
            )
            logger.info(f"Webhook set successfully: {webhook_url}")
            logger.info("🤖 Bot is ready to receive messages!")
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")
            # Don't fail the startup, just log the error
            logger.warning("Bot will continue without webhook setup")
        
    except Exception as e:
        logger.error(f"Error initializing bot: {e}")
        raise

async def shutdown_bot():
    """Shutdown bot gracefully"""
    global bot
    
    try:
        logger.info("Shutting down bot...")
        
        # Close payment providers
        try:
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

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    asyncio.create_task(shutdown_bot())
    sys.exit(0)

# Set up signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Initialize bot when the module is imported
# We'll initialize the bot manually since the app is created in bot.web.server

if __name__ == "__main__":
    import uvicorn
    
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    logger.info("Starting SMM Bot Web Server...")
    
    # Initialize bot before starting the server
    async def start_server():
        await initialize_bot()
        
        # Get port from environment or Railway's PORT variable
        port = int(os.environ.get("PORT", 8000))
        
        logger.info(f"Starting web server on 0.0.0.0:{port}")
        
        # Start server
        config = uvicorn.Config(
            "web_server:app",
            host="0.0.0.0",
            port=port,
            reload=settings.environment == "development",
            access_log=True,
            server_header=False,
            date_header=False
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    # Run the server
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

#!/usr/bin/env python3
"""
Main bot application with webhook support for Railway deployment
"""
import asyncio
import sys
import signal
import os
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from bot.config import settings
from bot.handlers import user_handlers, admin_handlers, admin_settings_handlers, support_handlers
from bot.middleware import SecurityMiddleware, LoggingMiddleware, LanguageMiddleware


# Global variables for cleanup
bot = None
dp = None
app = None

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
            from bot.database.db import db_manager
            await db_manager.close()
            logger.info("Database connection closed")
        except Exception as e:
            logger.warning(f"Error closing database: {e}")
        
        # Close bot session
        if bot:
            await bot.session.close()
        
        logger.info("Bot shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

async def setup_bot():
    """Setup bot and dispatcher"""
    global bot, dp
    
    try:
        # Initialize payment providers
        try:
            from bot.services.payment_service import payment_service
            logger.info("Payment providers initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize payment providers: {e}")
        
        # Initialize database
        try:
            from bot.database.db import db_manager
            success = await db_manager.initialize()
            if not success:
                logger.error("Database initialization failed")
                return False
            
            # Create tables if they don't exist
            success = await db_manager.create_tables()
            if not success:
                logger.error("Database table creation failed")
                return False
                
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False
        
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
            return False
        
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
            from bot.database.db import db_manager
            db = await db_manager.get_connection()
            try:
                await SettingsService.initialize_default_settings(db)
                logger.info("Default settings initialized")
            finally:
                await db_manager.pool.release(db)
        except Exception as e:
            logger.warning(f"Failed to initialize default settings: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up bot: {e}")
        return False

async def main():
    """Main function for webhook deployment"""
    global app
    
    try:
        # Configure logging
        logger.remove()
        logger.add(
            sys.stdout,
            level="INFO",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        
        logger.info("Starting SMM Bot with webhook support for Railway...")
        
        # Setup bot
        if not await setup_bot():
            logger.error("Failed to setup bot")
            return
        
        # Get Railway URL
        railway_url = os.environ.get("RAILWAY_STATIC_URL")
        if not railway_url:
            logger.error("RAILWAY_STATIC_URL environment variable not set")
            return
        
        webhook_url = f"{railway_url}/webhook"
        logger.info(f"Setting webhook URL: {webhook_url}")
        
        # Set webhook
        try:
            await bot.set_webhook(
                url=webhook_url,
                secret_token=getattr(settings, 'webhook_secret', None),
                drop_pending_updates=True
            )
            logger.info("Webhook set successfully")
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")
            return
        
        # Create aiohttp app
        app = web.Application()
        
        # Setup webhook handler
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
            secret_token=getattr(settings, 'webhook_secret', None)
        )
        webhook_requests_handler.register(app, path="/webhook")
        
        # Setup web interface routes
        async def web_redirect(request):
            return web.Response(
                text='''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Elite JAP Bot</title>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f7fa; }
                        .container { max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                        .btn { background: #0088cc; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }
                        .status { color: #10b981; font-weight: bold; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>🚀 Elite JAP Bot</h1>
                        <p class="status">✅ Bot is running successfully!</p>
                        <p>Welcome to the premium SMM services platform</p>
                        <p>Please start the bot to access your dashboard:</p>
                        <a href="https://t.me/nimadirishqiladiganbot" class="btn">Start Bot</a>
                        <p><small>After starting the bot, you'll be able to access this dashboard</small></p>
                    </div>
                </body>
                </html>
                ''',
                content_type='text/html'
            )
        
        app.router.add_get("/", web_redirect)
        
        # Health check endpoint
        async def health_check(request):
            return web.json_response({
                "status": "healthy",
                "webhook_configured": True,
                "bot_username": settings.bot_username
            })
        
        app.router.add_get("/health", health_check)
        
        # Get port from Railway
        port = int(os.environ.get("PORT", 8000))
        host = "0.0.0.0"
        
        logger.info(f"🚀 Starting webhook server on {host}:{port}")
        logger.info(f"🤖 Bot is ready to receive webhook updates!")
        logger.info(f"🌐 Web interface available at: {railway_url}")
        
        # Start server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        # Keep running
        try:
            await asyncio.Future()  # Run forever
        except asyncio.CancelledError:
            logger.info("Server shutdown requested")
        finally:
            await runner.cleanup()
            await shutdown()
        
    except Exception as e:
        logger.error(f"Error starting webhook server: {e}")
        raise

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

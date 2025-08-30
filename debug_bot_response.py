#!/usr/bin/env python3
"""
Debug bot response issues
Check webhook status, test handlers, and diagnose problems
"""
import asyncio
import sys
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.database.db import initialize, create_tables
from bot.handlers import user_handlers, admin_handlers, admin_settings_handlers, support_handlers
from bot.middleware import SecurityMiddleware, LoggingMiddleware, LanguageMiddleware


async def debug_bot_response():
    """Debug bot response issues"""
    try:
        logger.info("🔍 Starting bot response debugging...")
        
        # Initialize database
        try:
            await initialize()
            await create_tables()
            logger.info("✅ Database initialized")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            return False
        
        # Initialize bot
        try:
            bot = Bot(
                token=settings.bot_token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
            )
            
            me = await bot.get_me()
            logger.info(f"✅ Bot initialized: @{me.username} (ID: {me.id})")
        except Exception as e:
            logger.error(f"❌ Bot initialization failed: {e}")
            return False
        
        # Initialize dispatcher
        try:
            dp = Dispatcher()
            
            # Register middleware
            dp.message.middleware(SecurityMiddleware())
            dp.callback_query.middleware(SecurityMiddleware())
            dp.message.middleware(LanguageMiddleware())
            dp.callback_query.middleware(LanguageMiddleware())
            dp.message.middleware(LoggingMiddleware())
            dp.callback_query.middleware(LoggingMiddleware())
            
            # Register handlers - try simple handlers first for testing
            try:
                from bot.handlers import simple_handlers
                dp.include_router(simple_handlers.router)
                logger.info("Simple handlers registered for testing")
            except Exception as e:
                logger.warning(f"Failed to register simple handlers: {e}")
            
            # Register main handlers
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
            
            logger.info("✅ Dispatcher and handlers registered")
        except Exception as e:
            logger.error(f"❌ Dispatcher setup failed: {e}")
            return False
        
        # Check webhook status
        try:
            webhook_info = await bot.get_webhook_info()
            logger.info("📡 Current webhook status:")
            logger.info(f"   URL: {webhook_info.url}")
            logger.info(f"   Pending updates: {webhook_info.pending_update_count}")
            logger.info(f"   Max connections: {webhook_info.max_connections}")
            logger.info(f"   Allowed updates: {webhook_info.allowed_updates}")
            
            if webhook_info.last_error_date:
                logger.warning(f"⚠️ Last error: {webhook_info.last_error_message}")
                logger.warning(f"⚠️ Error date: {webhook_info.last_error_date}")
            
            # Check if webhook URL matches expected
            expected_url = "https://smm-tg-service-production.up.railway.app/webhook"
            if webhook_info.url != expected_url:
                logger.warning(f"🔄 Webhook URL mismatch!")
                logger.warning(f"   Expected: {expected_url}")
                logger.warning(f"   Current:  {webhook_info.url}")
                
                # Fix webhook URL
                logger.info("🔧 Fixing webhook URL...")
                await bot.delete_webhook(drop_pending_updates=True)
                await asyncio.sleep(1)
                
                await bot.set_webhook(
                    url=expected_url,
                    drop_pending_updates=True,
                    allowed_updates=["message", "callback_query"]
                )
                
                new_webhook_info = await bot.get_webhook_info()
                logger.success(f"✅ Webhook URL updated: {new_webhook_info.url}")
            else:
                logger.success("✅ Webhook URL is correct")
                
        except Exception as e:
            logger.error(f"❌ Webhook check failed: {e}")
        
        # Test webhook endpoint accessibility
        logger.info("🌐 Testing webhook endpoint accessibility...")
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("https://smm-tg-service-production.up.railway.app/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.success("✅ Webhook endpoint is accessible")
                        logger.info(f"   Health check: {data}")
                        
                        if data.get("webhook_configured"):
                            logger.success("✅ Webhook is properly configured in server")
                        else:
                            logger.warning("⚠️ Webhook not configured in server")
                    else:
                        logger.warning(f"⚠️ Webhook endpoint returned status: {response.status}")
        except Exception as e:
            logger.error(f"❌ Webhook endpoint test failed: {e}")
        
        # Test handler registration
        logger.info("🧪 Testing handler registration...")
        try:
            # Check if handlers are properly registered
            message_handlers = len(dp.message.handlers)
            callback_handlers = len(dp.callback_query.handlers)
            
            logger.info(f"   Message handlers: {message_handlers}")
            logger.info(f"   Callback handlers: {callback_handlers}")
            
            if message_handlers > 0 and callback_handlers > 0:
                logger.success("✅ Handlers are properly registered")
            else:
                logger.warning("⚠️ Some handlers may not be registered")
                
        except Exception as e:
            logger.error(f"❌ Handler registration test failed: {e}")
        
        # Test bot commands
        logger.info("🤖 Testing bot commands...")
        try:
            commands = await bot.get_my_commands()
            logger.info(f"   Registered commands: {len(commands)}")
            for cmd in commands:
                logger.info(f"   /{cmd.command} - {cmd.description}")
                
        except Exception as e:
            logger.error(f"❌ Commands test failed: {e}")
        
        # Clear any pending updates that might be causing issues
        if webhook_info.pending_update_count > 0:
            logger.warning(f"⚠️ Found {webhook_info.pending_update_count} pending updates")
            logger.info("🧹 Clearing pending updates...")
            
            await bot.delete_webhook(drop_pending_updates=True)
            await asyncio.sleep(1)
            await bot.set_webhook(
                url="https://smm-tg-service-production.up.railway.app/webhook",
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query"]
            )
            logger.success("✅ Pending updates cleared")
        
        # Test web server integration
        logger.info("🔗 Testing web server integration...")
        try:
            from bot.web.server import set_bot_and_dispatcher, bot as server_bot, dp as server_dp
            
            # Set bot and dispatcher in server
            set_bot_and_dispatcher(bot, dp)
            
            if server_bot and server_dp:
                logger.success("✅ Bot and dispatcher set in web server")
            else:
                logger.warning("⚠️ Bot or dispatcher not properly set in web server")
                
        except Exception as e:
            logger.error(f"❌ Web server integration test failed: {e}")
        
        logger.success("🎉 Bot response debugging completed!")
        
        # Provide recommendations
        logger.info("\n📋 Recommendations:")
        logger.info("   1. Send a message to your bot now to test")
        logger.info("   2. Check Railway logs for any webhook errors")
        logger.info("   3. Verify webhook URL is accessible from internet")
        logger.info(f"   4. Test webhook URL: https://smm-tg-service-production.up.railway.app/webhook")
        logger.info("   5. Make sure Railway deployment is running")
        
        await bot.session.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Bot response debugging failed: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(debug_bot_response())
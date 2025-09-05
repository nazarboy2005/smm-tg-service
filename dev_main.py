#!/usr/bin/env python3
"""
Development main entry point for SMM Bot - FORCED POLLING MODE
"""
import asyncio
import sys
from loguru import logger

# Add the bot directory to the path
sys.path.append('bot')

from bot.config import settings
from bot.database.db import db_manager
from bot.bot import bot, dp
from bot.middleware.language_middleware import LanguageMiddleware
from bot.middleware.security_middleware import SecurityMiddleware, AdminOnlyMiddleware
from bot.handlers import (
    simple_handlers,
    user_handlers,
    admin_handlers,
    admin_settings_handlers,
    support_handlers
)
from bot.services import (
    user_service,
    balance_service,
    order_service,
    service_service,
    admin_service,
    settings_service,
    referral_service,
    payment_service
)


async def main():
    """Main function to start the bot in development mode"""
    try:
        logger.info("🚀 Starting SMM Bot in DEVELOPMENT MODE (Polling)...")
        
        # Force polling mode for development
        settings.use_webhook = False
        logger.info("🔧 Forced POLLING mode for development")
        
        # Initialize database (with retry logic)
        logger.info("🗄️ Initializing Supabase database...")
        db_success = await db_manager.initialize()
        
        if not db_success:
            logger.warning("⚠️ Database initialization failed, but continuing with limited functionality")
            logger.warning("⚠️ Payment features may not work without database connection")
            logger.warning("⚠️ Please check your DATABASE_URL in .env file")
        else:
            logger.info("✅ Supabase database initialized successfully")
        
        # Initialize admin service manager
        logger.info("🔧 Initializing admin service manager...")
        from bot.services.admin_service import admin_service_manager
        await admin_service_manager.initialize()
        logger.info("✅ Admin service manager initialized successfully")
        
        # Initialize middleware
        logger.info("🔧 Setting up middleware...")
        dp.message.middleware(LanguageMiddleware())
        dp.message.middleware(SecurityMiddleware())
        dp.callback_query.middleware(LanguageMiddleware())
        dp.callback_query.middleware(SecurityMiddleware())
        
        # Initialize handlers
        logger.info("🎯 Setting up handlers...")
        simple_handlers.setup(dp)
        user_handlers.setup(dp)
        admin_handlers.setup(dp)
        admin_settings_handlers.setup(dp)
        support_handlers.setup(dp)
        
        # Payment service is already initialized during import
        
        logger.info("🎉 Bot setup completed successfully!")
        logger.info("🤖 Starting bot in POLLING mode...")
        logger.info("📱 Bot will respond to messages and commands")
        logger.info("🛑 Press Ctrl+C to stop the bot")
        
        # Start polling
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"💥 Fatal error starting bot: {e}")
        raise
    finally:
        # Cleanup
        logger.info("🧹 Cleaning up...")
        try:
            await db_manager.close()
            logger.info("✅ Database connections closed")
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)

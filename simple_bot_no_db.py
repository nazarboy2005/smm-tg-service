#!/usr/bin/env python3
"""
Simple SMM Bot - No Database Dependencies
"""
import asyncio
import sys
from loguru import logger

# Add the bot directory to the path
sys.path.append('bot')

from bot.config import settings
from bot.bot import bot, dp
from bot.handlers.simple_handlers import setup as setup_simple_handlers


async def main():
    """Main function to start the bot in simple mode"""
    try:
        logger.info("🚀 Starting Simple SMM Bot (No Database)...")
        
        # Force polling mode for development
        settings.use_webhook = False
        logger.info("🔧 Forced POLLING mode for development")
        
        # Setup only simple handlers (no database required)
        logger.info("🎯 Setting up simple handlers...")
        setup_simple_handlers(dp)
        
        logger.info("🎉 Bot setup completed successfully!")
        logger.info("🤖 Starting bot in POLLING mode...")
        logger.info("📱 Bot will respond to basic commands")
        logger.info("🛑 Press Ctrl+C to stop the bot")
        
        # Start polling
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"💥 Fatal error starting bot: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)

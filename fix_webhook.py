#!/usr/bin/env python3
"""
Script to delete webhook and switch to polling mode
"""
import asyncio
import sys
from loguru import logger

# Add the bot directory to the path
sys.path.insert(0, '.')

from bot.config import settings
from aiogram import Bot

async def delete_webhook():
    """Delete webhook and switch to polling mode"""
    try:
        logger.info("🔧 Deleting webhook to switch to polling mode...")
        
        # Create bot instance
        bot = Bot(token=settings.bot_token)
        
        # Get current webhook info
        webhook_info = await bot.get_webhook_info()
        logger.info(f"Current webhook URL: {webhook_info.url}")
        
        # Delete webhook
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook deleted successfully")
        
        # Verify webhook is deleted
        webhook_info = await bot.get_webhook_info()
        logger.info(f"New webhook URL: {webhook_info.url}")
        
        await bot.session.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error deleting webhook: {e}")
        return False

async def main():
    """Main function"""
    try:
        logger.info("🚀 Starting webhook deletion...")
        
        success = await delete_webhook()
        
        if success:
            logger.info("✅ Webhook deleted! Bot can now use polling mode.")
            logger.info("💡 You can now run: python test_simple_bot.py")
        else:
            logger.error("❌ Failed to delete webhook")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

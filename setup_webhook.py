#!/usr/bin/env python3
"""
Script to set up webhook for production
"""
import asyncio
import sys
from loguru import logger

# Add the bot directory to the path
sys.path.insert(0, '.')

from bot.config import settings
from aiogram import Bot

async def setup_webhook():
    """Set up webhook for production"""
    try:
        logger.info("🔧 Setting up webhook for production...")
        
        # Create bot instance
        bot = Bot(token=settings.bot_token)
        
        # Get current webhook info
        webhook_info = await bot.get_webhook_info()
        logger.info(f"Current webhook URL: {webhook_info.url}")
        
        # Set webhook for production
        webhook_url = "https://smm-tg-service-production.up.railway.app/webhook"
        
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"]
        )
        
        # Verify webhook is set
        webhook_info = await bot.get_webhook_info()
        logger.info(f"New webhook URL: {webhook_info.url}")
        
        if webhook_info.url == webhook_url:
            logger.info("✅ Webhook set successfully for production!")
            logger.info("🤖 Bot is now ready to receive updates via webhook")
        else:
            logger.error("❌ Failed to set webhook correctly")
        
        await bot.session.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error setting up webhook: {e}")
        return False

async def main():
    """Main function"""
    try:
        logger.info("🚀 Setting up webhook for production...")
        
        success = await setup_webhook()
        
        if success:
            logger.info("✅ Webhook setup completed!")
            logger.info("💡 You can now run: python main.py")
        else:
            logger.error("❌ Failed to set up webhook")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

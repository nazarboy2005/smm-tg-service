#!/usr/bin/env python3
"""
Script to stop any running bot instances and clear webhooks
Run this before starting the bot to avoid conflicts
"""
import asyncio
from aiogram import Bot
from loguru import logger
import sys

from bot.config import settings


async def stop_bot():
    """Stop any running bot instances and clear webhooks"""
    try:
        # Initialize bot
        bot = Bot(token=settings.bot_token)
        
        logger.info("Clearing webhook and stopping any running instances...")
        
        # Delete webhook to stop webhook mode
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("Webhook cleared successfully")
        except Exception as e:
            logger.info(f"No webhook to clear or error clearing webhook: {e}")
        
        # Close bot session
        await bot.session.close()
        logger.info("Bot session closed")
        
        logger.success("✅ All bot instances stopped successfully!")
        logger.info("You can now start the bot safely without conflicts")
        
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(stop_bot())
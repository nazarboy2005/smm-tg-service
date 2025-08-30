#!/usr/bin/env python3
"""
Debug webhook issues for the bot
Check webhook status, clear if needed, and diagnose problems
"""
import asyncio
from loguru import logger
from aiogram import Bot
from bot.config import settings


async def debug_webhook():
    """Debug webhook configuration"""
    try:
        logger.info("🔍 Starting webhook debugging...")
        
        # Initialize bot
        bot = Bot(token=settings.bot_token)
        
        # Get bot info
        me = await bot.get_me()
        logger.info(f"🤖 Bot: @{me.username} (ID: {me.id})")
        
        # Check current webhook status
        webhook_info = await bot.get_webhook_info()
        logger.info("📡 Current webhook status:")
        logger.info(f"   URL: {webhook_info.url}")
        logger.info(f"   Pending updates: {webhook_info.pending_update_count}")
        logger.info(f"   Max connections: {webhook_info.max_connections}")
        logger.info(f"   Allowed updates: {webhook_info.allowed_updates}")
        
        if webhook_info.last_error_date:
            logger.warning(f"⚠️ Last error: {webhook_info.last_error_message}")
            logger.warning(f"⚠️ Error date: {webhook_info.last_error_date}")
        
        # Check if webhook URL matches our settings
        expected_url = f"{settings.webhook_url}/webhook"
        if webhook_info.url != expected_url:
            logger.warning(f"🔄 Webhook URL mismatch!")
            logger.warning(f"   Expected: {expected_url}")
            logger.warning(f"   Current:  {webhook_info.url}")
            
            # Fix webhook URL
            logger.info("🔧 Fixing webhook URL...")
            await bot.delete_webhook(drop_pending_updates=True)
            await asyncio.sleep(2)
            
            await bot.set_webhook(
                url=expected_url,
                drop_pending_updates=True,
                secret_token=settings.webhook_secret if hasattr(settings, 'webhook_secret') and settings.webhook_secret else None
            )
            
            # Verify fix
            new_webhook_info = await bot.get_webhook_info()
            logger.success(f"✅ Webhook URL updated: {new_webhook_info.url}")
        
        # Test webhook endpoint
        logger.info("🌐 Testing webhook endpoint accessibility...")
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{settings.webhook_url}/") as response:
                    if response.status == 200:
                        logger.success("✅ Webhook endpoint is accessible")
                    else:
                        logger.warning(f"⚠️ Webhook endpoint returned status: {response.status}")
        except Exception as e:
            logger.error(f"❌ Webhook endpoint test failed: {e}")
        
        # Check for pending updates
        if webhook_info.pending_update_count > 0:
            logger.warning(f"⚠️ Found {webhook_info.pending_update_count} pending updates")
            logger.info("🧹 Clearing pending updates...")
            await bot.delete_webhook(drop_pending_updates=True)
            await bot.set_webhook(
                url=expected_url,
                drop_pending_updates=True,
                secret_token=settings.webhook_secret if hasattr(settings, 'webhook_secret') and settings.webhook_secret else None
            )
            logger.success("✅ Pending updates cleared")
        
        await bot.session.close()
        logger.success("🎉 Webhook debugging completed!")
        
        # Provide recommendations
        logger.info("📝 Recommendations:")
        logger.info("   1. Send /ping to @nimadirishqiladiganbot to test")
        logger.info("   2. Check Railway deployment logs")
        logger.info("   3. Verify webhook URL is accessible from internet")
        logger.info(f"   4. Test webhook URL: {expected_url}")
        
    except Exception as e:
        logger.error(f"❌ Webhook debugging failed: {e}")


if __name__ == "__main__":
    asyncio.run(debug_webhook())
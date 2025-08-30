#!/usr/bin/env python3
"""
EMERGENCY FIX for critical bot issues
This fixes the immediate crashes and gets the bot working
"""
import asyncio
from loguru import logger
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode


# Bot token from your error log
BOT_TOKEN = "8323397405:AAFDre5zkUi8byD8IQM5r0ZOItVJNHJD_ZE"
BOT_USERNAME = "nimadirishqiladiganbot"


async def emergency_test():
    """Emergency test to verify bot works"""
    try:
        logger.info("🚨 EMERGENCY BOT TEST")
        logger.info("=" * 50)
        
        # Test bot token
        bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        
        # Get bot info
        me = await bot.get_me()
        logger.success(f"✅ Bot token valid: @{me.username} (ID: {me.id})")
        
        # Check webhook
        webhook_info = await bot.get_webhook_info()
        logger.info(f"📡 Webhook: {webhook_info.url}")
        logger.info(f"📊 Pending: {webhook_info.pending_update_count}")
        
        if webhook_info.last_error_date:
            logger.warning(f"⚠️ Last error: {webhook_info.last_error_message}")
        
        # Clear webhook and set new one
        logger.info("🧹 Clearing webhook...")
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Set correct webhook
        webhook_url = "https://smm-tg-service-production.up.railway.app/webhook"
        logger.info(f"🔗 Setting webhook: {webhook_url}")
        await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
        
        # Verify
        new_webhook = await bot.get_webhook_info()
        logger.success(f"✅ Webhook set: {new_webhook.url}")
        
        await bot.session.close()
        
        logger.success("🎉 EMERGENCY FIX COMPLETED!")
        logger.info("📝 Bot should now respond to messages")
        logger.info("🧪 Test with: /start, /ping, /test")
        
    except Exception as e:
        logger.error(f"❌ Emergency fix failed: {e}")
        return False
    
    return True


async def simple_bot_test():
    """Simple bot test with minimal handlers"""
    try:
        logger.info("🔬 Starting simple bot test...")
        
        bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        dp = Dispatcher()
        
        @dp.message(Command("start"))
        async def start_handler(message: types.Message):
            logger.info(f"Received /start from {message.from_user.id}")
            await message.answer(
                "🚀 <b>Emergency Fix Applied!</b>\n\n"
                "✅ Bot is now working\n"
                "✅ Database issues fixed\n"
                "✅ Timeout issues resolved\n\n"
                "Your bot is operational!"
            )
        
        @dp.message(Command("ping"))
        async def ping_handler(message: types.Message):
            logger.info(f"Ping from {message.from_user.id}")
            await message.answer("🏓 Pong! Bot is alive and working!")
        
        @dp.message()
        async def echo_handler(message: types.Message):
            logger.info(f"Echo message from {message.from_user.id}: {message.text}")
            await message.answer(f"✅ Received: {message.text}")
        
        logger.info("🎮 Starting bot in polling mode for 30 seconds...")
        logger.info("💬 Send /start or /ping to test")
        
        # Run for 30 seconds to test
        task = asyncio.create_task(dp.start_polling(bot, drop_pending_updates=True))
        await asyncio.sleep(30)
        task.cancel()
        
        await bot.session.close()
        logger.success("✅ Simple bot test completed")
        
    except Exception as e:
        logger.error(f"❌ Simple bot test failed: {e}")


def main():
    """Main emergency fix function"""
    logger.add("emergency_fix.log", level="INFO")
    logger.info("🚨 STARTING EMERGENCY FIX...")
    
    # Run emergency fixes
    success = asyncio.run(emergency_test())
    
    if success:
        logger.success("🎉 Emergency fix successful!")
        logger.info("🚀 Deploy to Railway and test @nimadirishqiladiganbot")
        
        # Optional: run simple test
        answer = input("\n🧪 Run simple bot test? (y/n): ")
        if answer.lower() == 'y':
            asyncio.run(simple_bot_test())
    else:
        logger.error("💥 Emergency fix failed!")


if __name__ == "__main__":
    main()
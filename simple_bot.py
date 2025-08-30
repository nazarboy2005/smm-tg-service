"""
Simple working bot - minimal configuration
"""
import asyncio
import sys
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.filters import Command

# Simple bot token - replace with your actual token
BOT_TOKEN = "8323397405:AAFDre5zkUi8byD8IQM5r0ZOItVJNHJD_ZE"

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

# Create bot and dispatcher
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Simple handlers
@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command"""
    try:
        user_name = message.from_user.first_name or "User"
        await message.answer(
            f"🎉 <b>Welcome {user_name}!</b>\n\n"
            f"🚀 This is the Elite JAP Bot - your premium SMM services platform!\n\n"
            f"📋 <b>Available commands:</b>\n"
            f"• /start - Show this welcome message\n"
            f"• /help - Show help information\n"
            f"• /ping - Test bot responsiveness\n"
            f"• /balance - Check your balance\n"
            f"• /services - View available services\n"
            f"• /orders - View your orders\n\n"
            f"💎 Start using our premium services today!",
            parse_mode="HTML"
        )
        logger.info(f"User {message.from_user.id} (@{message.from_user.username}) started the bot")
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    try:
        await message.answer(
            "📚 <b>Bot Help</b>\n\n"
            "🔹 <b>Basic Commands:</b>\n"
            "• /start - Welcome message\n"
            "• /help - This help message\n"
            "• /ping - Test bot response\n\n"
            "🔹 <b>Account Commands:</b>\n"
            "• /balance - Check your balance\n"
            "• /profile - View your profile\n\n"
            "🔹 <b>Service Commands:</b>\n"
            "• /services - Browse services\n"
            "• /orders - View your orders\n"
            "• /new_order - Create new order\n\n"
            "🔹 <b>Support:</b>\n"
            "• /support - Contact support\n\n"
            "💡 <i>More features coming soon!</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@dp.message(Command("ping"))
async def cmd_ping(message: Message):
    """Handle /ping command"""
    try:
        await message.answer("🏓 <b>Pong!</b> Bot is online and responding! ✅", parse_mode="HTML")
        logger.info(f"Ping from user {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in ping command: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@dp.message(Command("balance"))
async def cmd_balance(message: Message):
    """Handle /balance command"""
    try:
        await message.answer(
            "💰 <b>Balance Information</b>\n\n"
            "🪙 <b>Current Balance:</b> 0 coins\n"
            "💵 <b>USD Value:</b> $0.00\n\n"
            "💳 <b>Payment Methods Available:</b>\n"
            "• PayPal\n"
            "• Cryptocurrency\n"
            "• Uzbek payment systems\n\n"
            "📈 <b>To add funds:</b>\n"
            "Use /deposit to add money to your account",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in balance command: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@dp.message(Command("services"))
async def cmd_services(message: Message):
    """Handle /services command"""
    try:
        await message.answer(
            "🛍️ <b>Available Services</b>\n\n"
            "📱 <b>Social Media Services:</b>\n"
            "• Instagram Followers\n"
            "• Instagram Likes\n"
            "• Instagram Views\n"
            "• TikTok Followers\n"
            "• TikTok Likes\n"
            "• YouTube Subscribers\n"
            "• YouTube Views\n\n"
            "🎯 <b>Popular Categories:</b>\n"
            "• Instagram Growth\n"
            "• TikTok Promotion\n"
            "• YouTube Marketing\n"
            "• Twitter Services\n\n"
            "💡 <i>Use /new_order to start ordering services!</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in services command: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@dp.message(Command("orders"))
async def cmd_orders(message: Message):
    """Handle /orders command"""
    try:
        await message.answer(
            "📋 <b>Your Orders</b>\n\n"
            "📊 <b>Order Statistics:</b>\n"
            "• Total Orders: 0\n"
            "• Completed: 0\n"
            "• Pending: 0\n"
            "• Cancelled: 0\n\n"
            "📝 <b>Recent Orders:</b>\n"
            "No orders yet. Start by using /new_order!",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in orders command: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@dp.message(Command("deposit"))
async def cmd_deposit(message: Message):
    """Handle /deposit command"""
    try:
        await message.answer(
            "💳 <b>Deposit Funds</b>\n\n"
            "💰 <b>Minimum Deposit:</b> $1.00\n"
            "💎 <b>Maximum Deposit:</b> $1000.00\n\n"
            "🔄 <b>Available Payment Methods:</b>\n"
            "• PayPal\n"
            "• Bitcoin (BTC)\n"
            "• Ethereum (ETH)\n"
            "• Solana (SOL)\n"
            "• XRP\n"
            "• Dogecoin (DOGE)\n"
            "• TON Coin\n\n"
            "💡 <i>Contact support for deposit instructions!</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in deposit command: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@dp.message(Command("support"))
async def cmd_support(message: Message):
    """Handle /support command"""
    try:
        await message.answer(
            "🆘 <b>Support</b>\n\n"
            "📞 <b>Contact Information:</b>\n"
            "• Telegram: @support_username\n"
            "• Email: support@elitejap.com\n"
            "• Website: https://elitejap.com\n\n"
            "⏰ <b>Support Hours:</b>\n"
            "24/7 Available\n\n"
            "📝 <b>Before contacting support:</b>\n"
            "• Check /help for common questions\n"
            "• Include your order ID if applicable\n"
            "• Describe your issue clearly",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in support command: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@dp.message()
async def echo_message(message: Message):
    """Handle all other messages"""
    try:
        # Only respond to text messages
        if message.text:
            await message.answer(
                "🤖 <b>Bot Response</b>\n\n"
                f"📝 <b>Your message:</b> {message.text}\n\n"
                "💡 <b>Available commands:</b>\n"
                "• /start - Welcome message\n"
                "• /help - Show help\n"
                "• /ping - Test bot\n"
                "• /balance - Check balance\n"
                "• /services - View services\n"
                "• /orders - View orders\n"
                "• /deposit - Add funds\n"
                "• /support - Get help",
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Error in echo handler: {e}")

async def main():
    """Main function"""
    try:
        logger.info("Starting Simple Bot...")
        
        # Test bot token
        me = await bot.get_me()
        logger.info(f"Bot initialized successfully: @{me.username} (ID: {me.id})")
        
        # Start polling
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

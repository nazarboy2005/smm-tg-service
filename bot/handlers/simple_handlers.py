"""
Simple handlers for testing bot responsiveness without database
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from loguru import logger

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Simple start command without database"""
    try:
        logger.info(f"Start command from user {message.from_user.id}")
        
        welcome_text = f"🎉 <b>Welcome to SMM Services Bot!</b>\n\n"
        welcome_text += f"👋 Hello, {message.from_user.first_name or 'User'}!\n\n"
        welcome_text += f"🌟 <b>Premium Social Media Marketing Services</b>\n\n"
        welcome_text += f"📊 <b>What we offer:</b>\n"
        welcome_text += f"• Instagram Followers & Likes\n"
        welcome_text += f"• YouTube Views & Subscribers\n"
        welcome_text += f"• TikTok Followers & Views\n"
        welcome_text += f"• Twitter Followers & Retweets\n"
        welcome_text += f"• And much more!\n\n"
        welcome_text += f"💰 <b>Features:</b>\n"
        welcome_text += f"• Instant delivery\n"
        welcome_text += f"• 24/7 support\n"
        welcome_text += f"• Secure payments\n"
        welcome_text += f"• Money-back guarantee\n\n"
        welcome_text += f"💡 <i>Bot is working correctly!</i>"
        
        await message.answer(welcome_text)
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await message.answer("❌ An error occurred. Please try again.")


@router.message(Command("ping"))
async def cmd_ping(message: Message):
    """Simple ping command"""
    try:
        logger.info(f"Ping from user {message.from_user.id}")
        await message.answer("🏓 Pong! Bot is online and responding.")
    except Exception as e:
        logger.error(f"Error in ping command: {e}")


@router.message(Command("test"))
async def cmd_test(message: Message):
    """Test command"""
    try:
        user_info = f"👤 User: {message.from_user.first_name} {message.from_user.last_name or ''}\n"
        user_info += f"🆔 ID: {message.from_user.id}\n" 
        user_info += f"📱 Username: @{message.from_user.username}\n"
        user_info += f"🕐 Message ID: {message.message_id}"
        
        await message.answer(
            f"🧪 <b>Bot Test Results</b>\n\n"
            f"{user_info}\n\n"
            f"✅ Bot is working correctly!",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in test command: {e}")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Help command"""
    try:
        help_text = f"🤖 <b>Bot Help</b>\n\n"
        help_text += f"📋 <b>Available Commands:</b>\n"
        help_text += f"• /start - Start the bot\n"
        help_text += f"• /ping - Test bot responsiveness\n"
        help_text += f"• /test - Test bot functionality\n"
        help_text += f"• /help - Show this help message\n\n"
        help_text += f"💡 <i>Bot is working correctly!</i>"
        
        await message.answer(help_text)
    except Exception as e:
        logger.error(f"Error in help command: {e}")


# Commented out echo handler to prevent conflicts with command handlers
# @router.message()
# async def echo_handler(message: Message):
#     """Echo handler for any message"""
#     try:
#         logger.info(f"Echo from user {message.from_user.id}: {message.text}")
#         await message.answer(f"📝 You said: {message.text}")
#     except Exception as e:
#         logger.error(f"Error in echo handler: {e}")

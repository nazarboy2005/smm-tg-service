"""
Bot initialization and configuration
"""
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings

# Create bot instance
bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

# Create dispatcher
dp = Dispatcher()

# Bot info (will be populated when bot starts)
bot_info = None

async def get_bot_info():
    """Get bot information"""
    global bot_info
    if not bot_info:
        try:
            bot_info = await bot.get_me()
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed to get bot info: {e}")
            return None
    return bot_info

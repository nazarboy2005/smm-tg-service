#!/usr/bin/env python3
"""
Test bot connection and basic functionality
"""
import asyncio
from bot.config import settings
from aiogram import Bot

async def test_bot():
    """Test bot connection"""
    try:
        bot = Bot(token=settings.bot_token)
        me = await bot.get_me()
        print(f'✅ Bot connection successful: @{me.username} (ID: {me.id})')
        await bot.session.close()
        return True
    except Exception as e:
        print(f'❌ Bot connection failed: {e}')
        return False

if __name__ == "__main__":
    success = asyncio.run(test_bot())
    if success:
        print("🎉 Bot is ready to receive messages!")
    else:
        print("💥 Bot connection failed!")
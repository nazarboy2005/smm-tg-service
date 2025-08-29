"""
Language middleware for the bot to ensure consistent language usage
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from loguru import logger

from bot.database.db import get_db_session
from bot.services.user_service import UserService
from bot.utils.i18n import Language


class LanguageMiddleware(BaseMiddleware):
    """Middleware to manage user language preferences"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process language preferences"""
        
        # Extract user information
        user_id = None
        if isinstance(event, Update):
            if event.message:
                user_id = event.message.from_user.id
            elif event.callback_query:
                user_id = event.callback_query.from_user.id
        
        if user_id is None:
            return await handler(event, data)
        
        # Get user's language preference from database
        language = Language.ENGLISH  # Default language
        
        try:
            async with get_db_session() as db:
                user = await UserService.get_user_by_telegram_id(db, user_id)
                if user and user.language:
                    language = Language(user.language.value)
            
            # Add language to data context for handlers
            data["user_language"] = language
            
            logger.debug(f"User {user_id} language set to {language.value}")
            
        except Exception as e:
            logger.error(f"Error getting user language: {e}")
        
        # Continue processing
        return await handler(event, data)

"""
Security middleware for the bot
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, Message, CallbackQuery
from loguru import logger

from bot.utils.security import SecurityUtils, rate_limiter
from bot.config import settings


class SecurityMiddleware(BaseMiddleware):
    """Security middleware for rate limiting and input validation"""
    
    def __init__(self):
        super().__init__()
        self.blocked_users = set()  # In production, use Redis or database
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process security checks"""
        
        # Extract user information
        user_id = None
        if isinstance(event, Update):
            if event.message:
                user_id = event.message.from_user.id
            elif event.callback_query:
                user_id = event.callback_query.from_user.id
        
        if user_id is None:
            return await handler(event, data)
        
        # Check if user is blocked
        if user_id in self.blocked_users:
            SecurityUtils.log_security_event(
                "blocked_user_attempt",
                user_id=user_id,
                severity="WARNING"
            )
            return  # Don't process the update
        
        # Validate Telegram ID
        if not SecurityUtils.validate_telegram_id(user_id):
            SecurityUtils.log_security_event(
                "invalid_telegram_id",
                user_id=user_id,
                severity="ERROR"
            )
            return
        
        # Rate limiting
        rate_key = SecurityUtils.rate_limit_key(user_id, "general")
        if not rate_limiter.is_allowed(rate_key, max_requests=30, window_seconds=60):
            # Rate limit exceeded
            if isinstance(event, Update) and event.message:
                try:
                    await event.message.answer("⚠️ Too many requests. Please slow down.")
                except Exception:
                    pass  # Ignore if can't send message
            return
        
        # Input sanitization for messages
        if isinstance(event, Update) and event.message and event.message.text:
            original_text = event.message.text
            sanitized_text = SecurityUtils.sanitize_input(original_text, max_length=4096)
            
            if original_text != sanitized_text:
                SecurityUtils.log_security_event(
                    "input_sanitized",
                    user_id=user_id,
                    details={"original_length": len(original_text), "sanitized_length": len(sanitized_text)},
                    severity="INFO"
                )
                event.message.text = sanitized_text
        
        # Log user activity
        SecurityUtils.log_security_event(
            "user_activity",
            user_id=user_id,
            details={
                "update_type": type(event).__name__,
                "has_message": hasattr(event, 'message') and event.message is not None,
                "has_callback": hasattr(event, 'callback_query') and event.callback_query is not None
            },
            severity="INFO"
        )
        
        # Continue processing
        return await handler(event, data)
    
    def block_user(self, user_id: int, reason: str = "Security violation"):
        """Block user from using the bot"""
        self.blocked_users.add(user_id)
        SecurityUtils.log_security_event(
            "user_blocked",
            user_id=user_id,
            details={"reason": reason},
            severity="WARNING"
        )
    
    def unblock_user(self, user_id: int):
        """Unblock user"""
        self.blocked_users.discard(user_id)
        SecurityUtils.log_security_event(
            "user_unblocked",
            user_id=user_id,
            severity="INFO"
        )


class AdminOnlyMiddleware(BaseMiddleware):
    """Middleware to restrict access to admin-only features"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Check if user is admin"""
        
        user_id = None
        if isinstance(event, Update):
            if event.message:
                user_id = event.message.from_user.id
            elif event.callback_query:
                user_id = event.callback_query.from_user.id
        
        if user_id is None:
            return await handler(event, data)
        
        # Check if user is admin
        if user_id not in settings.admin_ids:
            SecurityUtils.log_security_event(
                "unauthorized_admin_access",
                user_id=user_id,
                severity="WARNING"
            )
            
            # Send access denied message
            if isinstance(event, Update):
                if event.message:
                    await event.message.answer("❌ Access denied. Admin privileges required.")
                elif event.callback_query:
                    await event.callback_query.answer("❌ Access denied", show_alert=True)
            
            return
        
        # User is admin, continue processing
        return await handler(event, data)


class LoggingMiddleware(BaseMiddleware):
    """Middleware for logging bot interactions"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Log bot interactions"""
        
        # Extract information for logging
        log_data = {
            "event_type": type(event).__name__,
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }
        
        if isinstance(event, Update):
            log_data["update_id"] = event.update_id
            
            if event.message:
                log_data.update({
                    "message_id": event.message.message_id,
                    "user_id": event.message.from_user.id,
                    "username": event.message.from_user.username,
                    "chat_id": event.message.chat.id,
                    "message_type": "text" if event.message.text else "other",
                    "has_text": bool(event.message.text)
                })
                
                if event.message.text and not event.message.text.startswith('/'):
                    # Don't log full message content for privacy, just indicate type
                    log_data["text_length"] = len(event.message.text)
            
            elif event.callback_query:
                log_data.update({
                    "callback_data": event.callback_query.data,
                    "user_id": event.callback_query.from_user.id,
                    "username": event.callback_query.from_user.username,
                    "message_id": event.callback_query.message.message_id if event.callback_query.message else None
                })
        
        # Log the interaction
        logger.info(f"Bot interaction: {log_data}")
        
        try:
            # Process the handler
            result = await handler(event, data)
            
            # Log successful processing
            logger.debug(f"Handler completed successfully for update {log_data.get('update_id', 'unknown')}")
            
            return result
            
        except Exception as e:
            # Log error
            logger.error(f"Handler error for update {log_data.get('update_id', 'unknown')}: {e}")
            
            # Send error message to user if possible
            if isinstance(event, Update):
                try:
                    if event.message:
                        await event.message.answer("❌ An error occurred. Please try again later.")
                    elif event.callback_query:
                        await event.callback_query.answer("❌ An error occurred", show_alert=True)
                except Exception:
                    pass  # Ignore if can't send error message
            
            # Re-raise the exception
            raise

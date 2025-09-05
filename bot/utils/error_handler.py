"""
Enhanced error handling utilities for the bot
"""
import traceback
from typing import Optional, Dict, Any
from loguru import logger
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError

from bot.utils.enhanced_i18n import get_text, Language


class BotError(Exception):
    """Base bot error class"""
    
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class DatabaseError(BotError):
    """Database related errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DATABASE_ERROR", details)


class ServiceError(BotError):
    """Service related errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "SERVICE_ERROR", details)


class PaymentError(BotError):
    """Payment related errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "PAYMENT_ERROR", details)


class ErrorHandler:
    """Enhanced error handler for the bot"""
    
    @staticmethod
    async def handle_message_error(message: Message, error: Exception, language: Language = Language.ENGLISH):
        """Handle errors in message handlers"""
        try:
            logger.error(f"Error in message handler for user {message.from_user.id}: {error}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Get user-friendly error message
            error_text = ErrorHandler._get_user_friendly_error(error, language)
            
            # Send error message to user
            await message.answer(error_text, parse_mode="HTML")
            
        except Exception as e:
            logger.error(f"Failed to handle message error: {e}")
            # Fallback error message
            try:
                await message.answer("❌ An unexpected error occurred. Please try again later.", parse_mode=None)
            except:
                pass
    
    @staticmethod
    async def handle_callback_error(callback: CallbackQuery, error: Exception, language: Language = Language.ENGLISH):
        """Handle errors in callback handlers"""
        try:
            logger.error(f"Error in callback handler for user {callback.from_user.id}: {error}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Get user-friendly error message
            error_text = ErrorHandler._get_user_friendly_error(error, language)
            
            # Send error message to user
            await callback.message.edit_text(error_text, parse_mode="HTML")
            await callback.answer("❌ Error occurred")
            
        except TelegramBadRequest:
            # Message might be too long or invalid, try to answer with callback
            try:
                await callback.answer("❌ Error occurred", show_alert=True)
            except:
                pass
        except Exception as e:
            logger.error(f"Failed to handle callback error: {e}")
            # Fallback error handling
            try:
                await callback.answer("❌ Error occurred", show_alert=True)
            except:
                pass
    
    @staticmethod
    def _get_user_friendly_error(error: Exception, language: Language = Language.ENGLISH) -> str:
        """Get user-friendly error message"""
        try:
            if isinstance(error, BotError):
                # Custom bot errors
                if error.error_code == "DATABASE_ERROR":
                    return get_text("error_occurred", language) + "\n\n💡 Please try again or contact support."
                elif error.error_code == "SERVICE_ERROR":
                    return get_text("service_not_found", language) + "\n\n💡 The service might be temporarily unavailable."
                elif error.error_code == "PAYMENT_ERROR":
                    return "💳 Payment Error\n\n💡 Please check your payment details and try again."
                else:
                    return get_text("error_occurred", language)
            
            elif isinstance(error, TelegramNetworkError):
                return "🌐 Network Error\n\n💡 Please check your internet connection and try again."
            
            elif isinstance(error, TelegramBadRequest):
                return "📱 Request Error\n\n💡 Please try again with a different input."
            
            else:
                # Generic error
                return get_text("error_occurred", language)
                
        except Exception as e:
            logger.error(f"Error in _get_user_friendly_error: {e}")
            return "❌ An error occurred. Please try again."
    
    @staticmethod
    def log_error(error: Exception, context: str = "", user_id: Optional[int] = None):
        """Log error with context"""
        try:
            error_info = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context,
                "user_id": user_id,
                "traceback": traceback.format_exc()
            }
            
            logger.error(f"Bot Error: {error_info}")
            
        except Exception as e:
            logger.error(f"Failed to log error: {e}")


# Decorator for error handling
def handle_errors(language: Language = Language.ENGLISH):
    """Decorator to handle errors in handlers"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as error:
                # Try to extract message or callback from args
                message = None
                callback = None
                
                for arg in args:
                    if isinstance(arg, Message):
                        message = arg
                        break
                    elif isinstance(arg, CallbackQuery):
                        callback = arg
                        break
                
                # Handle the error
                if message:
                    await ErrorHandler.handle_message_error(message, error, language)
                elif callback:
                    await ErrorHandler.handle_callback_error(callback, error, language)
                else:
                    ErrorHandler.log_error(error, f"Handler: {func.__name__}")
                
                return None
        
        return wrapper
    return decorator

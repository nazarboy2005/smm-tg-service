"""
Support handlers for the Telegram bot
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from bot.database.db import get_db
from bot.services.user_service import UserService
from bot.utils.i18n import get_text, Language

router = Router()


@router.callback_query(F.data == "support_contact")
async def handle_support_contact(callback: CallbackQuery, user_language: Language = None):
    """Handle support contact button"""
    try:
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                language = user_language or Language(user.language.value)
                
                text = f"📝 <b>Contact Support</b>\n\n"
                text += f"Our support team is ready to help you! Please choose a method to contact us:\n\n"
                text += f"1. <b>Telegram</b>: Send a direct message to @smmbot_support\n"
                text += f"2. <b>Email</b>: Send details to support@smmbot.com\n"
                text += f"3. <b>Live Chat</b>: Available on our website https://smmbot.com\n\n"
                text += f"<i>When contacting support, please include:</i>\n"
                text += f"• Your Telegram username or ID\n"
                text += f"• Order ID (if applicable)\n"
                text += f"• Detailed description of the issue\n"
                text += f"• Screenshots (if available)\n\n"
                text += f"<i>We'll respond within 2 hours.</i>"
                
                support_keyboard = InlineKeyboardBuilder()
                support_keyboard.button(
                    text=f"⬅️ Back to Support ⬅️",
                    callback_data="menu_support"
                )
                support_keyboard.adjust(1)
                
                await callback.message.edit_text(
                    text,
                    reply_markup=support_keyboard.as_markup()
                )
            break
    except Exception as e:
        logger.error(f"Error in support contact: {e}")
        await callback.answer("❌ Error loading contact information", show_alert=True)


@router.callback_query(F.data == "support_faq")
async def handle_support_faq(callback: CallbackQuery, user_language: Language = None):
    """Handle support FAQ button"""
    try:
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                language = user_language or Language(user.language.value)
                
                text = f"❓ <b>Frequently Asked Questions</b>\n\n"
                
                # Payment FAQs
                text += f"<b>Payment Issues</b>\n"
                text += f"Q: How long does it take to process payments?\n"
                text += f"A: Most payments are processed instantly. Crypto payments may take up to 30 minutes.\n\n"
                text += f"Q: Which payment methods are available?\n"
                text += f"A: We accept credit cards, cryptocurrency, and various local payment options.\n\n"
                
                # Orders FAQs
                text += f"<b>Order Issues</b>\n"
                text += f"Q: Why is my order pending?\n"
                text += f"A: Orders typically start within 5-30 minutes. High volumes may cause delays.\n\n"
                text += f"Q: What happens if my order is partially completed?\n"
                text += f"A: You'll receive a partial refund for the uncompleted portion.\n\n"
                
                # Service FAQs
                text += f"<b>Service Questions</b>\n"
                text += f"Q: Are your services safe?\n"
                text += f"A: Yes! Our services comply with platform guidelines and are low-risk.\n\n"
                text += f"Q: Do followers/likes drop?\n"
                text += f"A: Small fluctuations are normal. We offer refills for most services if needed.\n\n"
                
                # Technical FAQs
                text += f"<b>Technical Issues</b>\n"
                text += f"Q: Why am I getting an error when placing an order?\n"
                text += f"A: Check that your link is correct and your balance is sufficient.\n\n"
                text += f"Q: How do I change my language?\n"
                text += f"A: Go to Settings → Change Language in the main menu."
                
                support_keyboard = InlineKeyboardBuilder()
                support_keyboard.button(
                    text=f"⬅️ Back to Support ⬅️",
                    callback_data="menu_support"
                )
                support_keyboard.adjust(1)
                
                await callback.message.edit_text(
                    text,
                    reply_markup=support_keyboard.as_markup()
                )
            break
    except Exception as e:
        logger.error(f"Error in support FAQ: {e}")
        await callback.answer("❌ Error loading FAQ", show_alert=True)

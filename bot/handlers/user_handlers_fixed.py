"""
User handlers for the Telegram bot - FIXED VERSION
"""
import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from bot.database.db import get_db
from bot.database.models import UserLanguage, PaymentMethod, TransactionType
from bot.services.user_service import UserService
from bot.services.balance_service import BalanceService
from bot.services.service_service import ServiceService
from bot.services.order_service import OrderService
from bot.services.referral_service import ReferralService
from bot.services.payment_service import payment_service
from bot.services.settings_service import SettingsService
from bot.utils.i18n import get_text, Language
from bot.utils.keyboards import *
from bot.config import settings

router = Router()


# Add a simple test handler at the top to ensure basic functionality
@router.message(Command("ping"))
async def ping_command(message: Message):
    """Simple ping command to test bot responsiveness"""
    try:
        logger.info(f"Ping from user {message.from_user.id}: @{message.from_user.username}")
        await message.answer("🏓 Pong! Bot is online and responding.")
    except Exception as e:
        logger.error(f"Error in ping command: {e}")


@router.message(Command("test"))
async def test_command(message: Message):
    """Test command to verify bot functionality"""
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
        logger.error(f"Error handling /test command: {e}")


class OrderStates(StatesGroup):
    waiting_for_link = State()
    waiting_for_quantity = State()
    confirmation = State()


class PaymentStates(StatesGroup):
    waiting_for_amount = State()


# Command handlers
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, user_language: Language = None):
    """Handle /start command"""
    try:
        # Get database session using proper async context manager
        async for db in get_db():
            # Parse referral code from start parameter
            referral_code = None
            if message.text and len(message.text.split()) > 1:
                start_param = message.text.split()[1]
                if start_param.startswith("ref_"):
                    referral_code = start_param[4:]
                    logger.info(f"User {message.from_user.id} using referral code: {referral_code}")
            
            # Get or create user
            user = await UserService.create_user(
                db=db,
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                referred_by_code=referral_code
            )
            
            if not user:
                await message.answer("❌ Error creating user account. Please try again.", parse_mode=None)
                return
            
            # If new user, show language selection
            if not user.language or user.language == UserLanguage.ENGLISH:
                welcome_text = f"🎉 <b>Welcome to SMM Services Bot!</b>\n\n"
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
                welcome_text += f"🌐 <b>Please select your language:</b>"
                
                await message.answer(
                    welcome_text,
                    reply_markup=get_language_keyboard()
                )
            else:
                # Show main menu
                language = Language(user.language.value)
                balance = await BalanceService.get_user_balance(db, user.id)
                
                welcome_text = f"🎉 <b>Welcome back, {user.first_name or 'User'}!</b>\n\n"
                welcome_text += f"💰 <b>Your Balance:</b> {balance:,.0f} coins\n\n"
                welcome_text += f"📊 <b>Quick Actions:</b>\n"
                welcome_text += f"• Browse services\n"
                welcome_text += f"• Add balance\n"
                welcome_text += f"• Check orders\n"
                welcome_text += f"• View referrals\n\n"
                welcome_text += f"💡 <i>Select an option below to get started</i>"
                
                await message.answer(
                    welcome_text,
                    reply_markup=get_main_menu_keyboard(language, user.is_admin)
                )
            
            # Update user activity
            await UserService.update_user_activity(db, user.id)
            break
            
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await message.answer("❌ An error occurred. Please try again.", parse_mode=None)


# Callback query handlers
@router.callback_query(F.data.startswith("lang_"))
async def handle_language_selection(callback: CallbackQuery):
    """Handle language selection"""
    try:
        language_code = callback.data.split("_")[1]
        language = Language(language_code)
        user_language = UserLanguage(language_code)
        
        # Get database session using proper async context manager
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                await UserService.update_user_language(db, user.id, user_language)
                
                await callback.message.edit_text(
                    get_text("language_selected", language),
                    reply_markup=get_main_menu_keyboard(language, user.is_admin)
                )
            break
            
    except Exception as e:
        logger.error(f"Error in language selection: {e}")
        await callback.answer("❌ Error updating language")


@router.callback_query(F.data == "menu_main")
async def handle_main_menu(callback: CallbackQuery, user_language: Language = None):
    """Handle main menu"""
    try:
        # Get database session using proper async context manager
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                # Use middleware language or user language from DB
                language = user_language or Language(user.language.value)
                await callback.message.edit_text(
                    get_text("main_menu", language),
                    reply_markup=get_main_menu_keyboard(language, user.is_admin)
                )
            break
    except Exception as e:
        logger.error(f"Error in main menu: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data == "menu_balance")
async def handle_balance_menu(callback: CallbackQuery, user_language: Language = None):
    """Handle balance menu"""
    try:
        # Get database session
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                # Use middleware language or user language from DB
                language = user_language or Language(user.language.value)
                balance = await BalanceService.get_user_balance(db, user.id)
                
                # Get dynamic settings
                min_deposit = await SettingsService.get_setting(db, "min_deposit_usd", 1.0)
                max_deposit = await SettingsService.get_setting(db, "max_deposit_usd", 1000.0)
                coins_per_usd = await SettingsService.get_setting(db, "coins_per_usd", 1000)
                
                # Enhanced balance display
                text = f"💰 <b>Your Balance</b>\n\n"
                text += f"🪙 <b>Coins:</b> {balance:,.0f}\n"
                text += f"💵 <b>USD Value:</b> ${balance/coins_per_usd:.2f}\n\n"
                text += f"📊 <b>Deposit Limits:</b>\n"
                text += f"• Minimum: ${min_deposit} USD\n"
                text += f"• Maximum: ${max_deposit} USD\n"
                text += f"• Rate: {coins_per_usd:,} coins per $1 USD\n\n"
                text += f"💡 <i>Tap 'Add Balance' to deposit funds</i>"
                
                await callback.message.edit_text(
                    text,
                    reply_markup=get_balance_menu_keyboard(language)
                )
            break
    except Exception as e:
        logger.error(f"Error in balance menu: {e}")
        await callback.answer("❌ Error loading balance")


@router.callback_query(F.data == "balance_add")
async def handle_add_balance(callback: CallbackQuery):
    """Handle add balance"""
    try:
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                language = Language(user.language.value)
                
                await callback.message.edit_text(
                    get_text("choose_payment_method", language),
                    reply_markup=await get_payment_methods_keyboard(db, language)
                )
            break
    except Exception as e:
        logger.error(f"Error in add balance: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data.startswith("payment_"))
async def handle_payment_method(callback: CallbackQuery, state: FSMContext):
    """Handle payment method selection"""
    try:
        payment_method = callback.data.split("_")[1]
        
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                language = Language(user.language.value)
                
                # Store payment method in state
                await state.update_data(payment_method=payment_method)
                await state.set_state(PaymentStates.waiting_for_amount)
                
                # Get dynamic settings
                min_deposit = await SettingsService.get_setting(db, "min_deposit_usd", 1.0)
                max_deposit = await SettingsService.get_setting(db, "max_deposit_usd", 1000.0)
                
                await callback.message.edit_text(
                    get_text("enter_amount", language, 
                           min_usd=min_deposit, 
                           max_usd=max_deposit),
                    reply_markup=get_back_keyboard(language, "balance_add")
                )
            break
    except Exception as e:
        logger.error(f"Error in payment method: {e}")
        await callback.answer("❌ Error")


@router.message(StateFilter(PaymentStates.waiting_for_amount))
async def handle_payment_amount(message: Message, state: FSMContext):
    """Handle payment amount input"""
    try:
        # Validate amount
        try:
            amount = float(message.text.strip())
        except ValueError:
            async for db in get_db():
                user = await UserService.get_user_by_telegram_id(db, message.from_user.id)
                if user:
                    language = Language(user.language.value)
                    min_deposit = await SettingsService.get_setting(db, "min_deposit_usd", 1.0)
                    max_deposit = await SettingsService.get_setting(db, "max_deposit_usd", 1000.0)
                    await message.answer(
                        get_text("invalid_amount", language, 
                               min_usd=min_deposit, 
                               max_usd=max_deposit)
                    )
                break
            return
        
        async for db in get_db():
            # Check amount limits with dynamic settings
            min_deposit = await SettingsService.get_setting(db, "min_deposit_usd", 1.0)
            max_deposit = await SettingsService.get_setting(db, "max_deposit_usd", 1000.0)
            
            if amount < min_deposit or amount > max_deposit:
                user = await UserService.get_user_by_telegram_id(db, message.from_user.id)
                if user:
                    language = Language(user.language.value)
                    await message.answer(
                        get_text("invalid_amount", language, 
                               min_usd=min_deposit, 
                               max_usd=max_deposit)
                    )
                break
            
            # Get payment method from state
            data = await state.get_data()
            payment_method = data.get("payment_method")
            
            if not payment_method:
                await message.answer("❌ Payment method not found. Please start again.", parse_mode=None)
                await state.clear()
                return
            
            user = await UserService.get_user_by_telegram_id(db, message.from_user.id)
            if user:
                language = Language(user.language.value)
                
                # Create payment
                result = await payment_service.create_payment(
                    db=db,
                    provider_name=payment_method,
                    user_id=user.id,
                    amount_usd=amount,
                    description=f"Balance top-up via {payment_method}"
                )
                
                if result and result.success:
                    coins_amount = await BalanceService.usd_to_coins(db, amount)
                    
                    if result.payment_url:
                        # Send payment link
                        await message.answer(
                            f"💳 <b>Payment created!</b>\n"
                            f"💰 Amount: ${amount} USD ({coins_amount} coins)\n"
                            f"🔗 Payment link: {result.payment_url}\n\n"
                            f"⏳ Complete the payment and your balance will be updated automatically."
                        )
                    else:
                        await message.answer(
                            f"💳 <b>Payment created!</b>\n"
                            f"💰 Amount: ${amount} USD ({coins_amount} coins)\n"
                            f"Payment ID: {result.payment_id}\n\n"
                            f"⏳ Please complete the payment."
                        )
                else:
                    error_msg = result.error_message if result else "Payment creation failed"
                    await message.answer(f"❌ {error_msg}", parse_mode=None)
                
                await state.clear()
            break
            
    except Exception as e:
        logger.error(f"Error in payment amount: {e}")
        await message.answer("❌ Error processing payment", parse_mode=None)
        await state.clear()


# Continue with all other handlers using the same pattern...
# For brevity, I'll include just a few more key handlers

@router.callback_query(F.data == "menu_services")
async def handle_services_menu(callback: CallbackQuery):
    """Handle services menu"""
    try:
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                language = Language(user.language.value)
                categories = await ServiceService.get_active_categories(db)
                
                if categories:
                    await callback.message.edit_text(
                        get_text("choose_category", language),
                        reply_markup=get_service_categories_keyboard(categories, language)
                    )
                else:
                    # Create demo categories and services when none are available
                    await ServiceService.create_demo_categories_and_services(db)
                    
                    # Try to fetch again
                    categories = await ServiceService.get_active_categories(db)
                    
                    if categories:
                        await callback.message.edit_text(
                            get_text("choose_category", language),
                            reply_markup=get_service_categories_keyboard(categories, language)
                        )
                    else:
                        await callback.message.edit_text(
                            get_text("no_services", language),
                            reply_markup=get_back_keyboard(language)
                        )
            break
    except Exception as e:
        logger.error(f"Error in services menu: {e}")
        await callback.answer("❌ Error")


# Sticker handlers
@router.message(F.sticker)
async def handle_sticker(message: Message):
    """Handle sticker messages with appropriate responses"""
    try:
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, message.from_user.id)
            if user:
                language = Language(user.language.value)
                
                # Respond with a fun message and show main menu
                sticker_responses = [
                    get_text("sticker_response_1", language),
                    get_text("sticker_response_2", language),
                    get_text("sticker_response_3", language)
                ]
                
                import random
                response = random.choice(sticker_responses)
                
                await message.answer(
                    response,
                    reply_markup=get_main_menu_keyboard(language, user.is_admin)
                )
            break
    except Exception as e:
        logger.error(f"Error handling sticker: {e}")


# Add all other handlers following the same pattern...
# This is a template showing the correct database session usage
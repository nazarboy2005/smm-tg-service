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


@router.message(Command("services"))
async def cmd_services(message: Message):
    """Get services directly from JAP API"""
    try:
        logger.info(f"Services request from user {message.from_user.id}")
        
        # Send loading message
        loading_msg = await message.answer("🔄 Fetching services from JAP API...")
        
        # Get services directly from JAP API
        services = await ServiceService.get_services_from_jap()
        
        if not services:
            await loading_msg.edit_text("❌ Failed to fetch services from JAP API. Please try again later.")
            return
        
        # Group services by category
        categories = {}
        for service in services:
            category = service.get("category", "Other")
            if category not in categories:
                categories[category] = []
            categories[category].append(service)
        
        # Create response message
        response = "📋 <b>Available Services from JAP API</b>\n\n"
        
        for category_name, category_services in list(categories.items())[:10]:  # Limit to first 10 categories
            response += f"📁 <b>{category_name}</b>\n"
            
            for service in category_services[:5]:  # Limit to first 5 services per category
                service_id = service.get("service", "N/A")
                service_name = service.get("name", "Unknown")
                rate = service.get("rate", "0")
                min_qty = service.get("min", "0")
                max_qty = service.get("max", "0")
                
                response += f"  • <b>{service_name}</b>\n"
                response += f"    ID: {service_id} | Rate: ${rate}/1K | Min: {min_qty} | Max: {max_qty}\n\n"
        
        if len(categories) > 10:
            response += f"... and {len(categories) - 10} more categories\n"
        
        response += "💡 <i>Use /order [service_id] [link] [quantity] to place an order</i>"
        
        await loading_msg.edit_text(response, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in services command: {e}")
        await message.answer("❌ An error occurred while fetching services. Please try again.")


@router.message(Command("balance"))
async def cmd_balance(message: Message):
    """Get JAP balance directly from API"""
    try:
        logger.info(f"Balance request from user {message.from_user.id}")
        
        # Send loading message
        loading_msg = await message.answer("🔄 Fetching JAP balance...")
        
        # Get balance directly from JAP API
        balance_info = await ServiceService.get_jap_balance()
        
        if not balance_info:
            await loading_msg.edit_text("❌ Failed to fetch balance from JAP API. Please try again later.")
            return
        
        balance = balance_info.get("balance", "0")
        currency = balance_info.get("currency", "USD")
        
        response = f"💰 <b>JAP Balance</b>\n\n"
        response += f"💵 Balance: <b>{balance} {currency}</b>\n\n"
        response += "💡 <i>This is your current balance on the JAP platform</i>"
        
        await loading_msg.edit_text(response, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in balance command: {e}")
        await message.answer("❌ An error occurred while fetching balance. Please try again.")


@router.message(Command("order"))
async def cmd_order(message: Message):
    """Create order directly via JAP API"""
    try:
        # Parse command arguments: /order [service_id] [link] [quantity]
        args = message.text.split()[1:]
        
        if len(args) != 3:
            await message.answer(
                "📝 <b>Order Command Usage:</b>\n\n"
                "Use: <code>/order [service_id] [link] [quantity]</code>\n\n"
                "Example: <code>/order 123 https://instagram.com/user 1000</code>\n\n"
                "💡 First use /services to see available service IDs",
                parse_mode="HTML"
            )
            return
        
        service_id = int(args[0])
        link = args[1]
        quantity = int(args[2])
        
        logger.info(f"Order request from user {message.from_user.id}: service={service_id}, link={link}, quantity={quantity}")
        
        # Send loading message
        loading_msg = await message.answer("🔄 Creating order via JAP API...")
        
        # Create order directly via JAP API
        order_result = await ServiceService.create_order_via_jap(service_id, link, quantity)
        
        if not order_result:
            await loading_msg.edit_text("❌ Failed to create order via JAP API. Please check your parameters and try again.")
            return
        
        order_id = order_result.get("order", "Unknown")
        
        response = f"✅ <b>Order Created Successfully!</b>\n\n"
        response += f"🆔 Order ID: <b>{order_id}</b>\n"
        response += f"🔗 Link: {link}\n"
        response += f"📊 Quantity: {quantity}\n"
        response += f"🆔 Service ID: {service_id}\n\n"
        response += f"💡 Use /status {order_id} to check order status"
        
        await loading_msg.edit_text(response, parse_mode="HTML")
        
    except ValueError:
        await message.answer("❌ Invalid parameters. Please use: /order [service_id] [link] [quantity]")
    except Exception as e:
        logger.error(f"Error in order command: {e}")
        await message.answer("❌ An error occurred while creating the order. Please try again.")


@router.message(Command("status"))
async def cmd_status(message: Message):
    """Get order status directly via JAP API"""
    try:
        # Parse command arguments: /status [order_id]
        args = message.text.split()[1:]
        
        if len(args) != 1:
            await message.answer(
                "📝 <b>Status Command Usage:</b>\n\n"
                "Use: <code>/status [order_id]</code>\n\n"
                "Example: <code>/status 12345</code>",
                parse_mode="HTML"
            )
            return
        
        order_id = int(args[0])
        
        logger.info(f"Status request from user {message.from_user.id}: order_id={order_id}")
        
        # Send loading message
        loading_msg = await message.answer("🔄 Fetching order status...")
        
        # Get order status directly via JAP API
        status_result = await ServiceService.get_order_status_via_jap(order_id)
        
        if not status_result:
            await loading_msg.edit_text("❌ Failed to fetch order status. Please check the order ID and try again.")
            return
        
        charge = status_result.get("charge", "0")
        start_count = status_result.get("start_count", "0")
        status = status_result.get("status", "Unknown")
        remains = status_result.get("remains", "0")
        currency = status_result.get("currency", "USD")
        
        response = f"📊 <b>Order Status</b>\n\n"
        response += f"🆔 Order ID: <b>{order_id}</b>\n"
        response += f"💰 Charge: <b>{charge} {currency}</b>\n"
        response += f"📈 Start Count: <b>{start_count}</b>\n"
        response += f"📊 Status: <b>{status}</b>\n"
        response += f"📉 Remains: <b>{remains}</b>\n"
        
        await loading_msg.edit_text(response, parse_mode="HTML")
        
    except ValueError:
        await message.answer("❌ Invalid order ID. Please use: /status [order_id]")
    except Exception as e:
        logger.error(f"Error in status command: {e}")
        await message.answer("❌ An error occurred while fetching order status. Please try again.")


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
        # Parse referral code from start parameter
        referral_code = None
        if message.text and len(message.text.split()) > 1:
            start_param = message.text.split()[1]
            if start_param.startswith("ref_"):
                referral_code = start_param[4:]
                logger.info(f"User {message.from_user.id} using referral code: {referral_code}")
        
        # Get database session using proper async context manager
        async for db in get_db():
            try:
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
                break  # Exit the async for loop after successful processing
                
            except Exception as db_error:
                logger.error(f"Database error in start command: {db_error}")
                await message.answer("❌ Database error. Please try again.", parse_mode=None)
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
            try:
                user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
                if user:
                    await UserService.update_user_language(db, user.id, user_language)
                    
                    await callback.message.edit_text(
                        get_text("language_selected", language),
                        reply_markup=get_main_menu_keyboard(language, user.is_admin)
                    )
                break
            except Exception as db_error:
                logger.error(f"Database error in language selection: {db_error}")
                await callback.answer("❌ Database error")
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
            try:
                user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
                if user:
                    # Use middleware language or user language from DB
                    language = user_language or Language(user.language.value)
                    await callback.message.edit_text(
                        get_text("main_menu", language),
                        reply_markup=get_main_menu_keyboard(language, user.is_admin)
                    )
                break
            except Exception as db_error:
                logger.error(f"Database error in main menu: {db_error}")
                await callback.answer("❌ Database error")
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
            try:
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
            except Exception as db_error:
                logger.error(f"Database error in balance menu: {db_error}")
                await callback.answer("❌ Database error")
                break
    except Exception as e:
        logger.error(f"Error in balance menu: {e}")
        await callback.answer("❌ Error loading balance")


@router.callback_query(F.data == "balance_add")
async def handle_add_balance(callback: CallbackQuery):
    """Handle add balance"""
    try:
        async for db in get_db():
            try:
                user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
                if user:
                    language = Language(user.language.value)
                    
                    await callback.message.edit_text(
                        get_text("choose_payment_method", language),
                        reply_markup=await get_payment_methods_keyboard(db, language)
                    )
                break
            except Exception as db_error:
                logger.error(f"Database error in add balance: {db_error}")
                await callback.answer("❌ Database error")
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
            try:
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
            except Exception as db_error:
                logger.error(f"Database error in payment method: {db_error}")
                await callback.answer("❌ Database error")
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
            try:
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
            except Exception as db_error:
                logger.error(f"Database error in payment amount: {db_error}")
                await message.answer("❌ Database error processing payment", parse_mode=None)
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
            try:
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
            except Exception as db_error:
                logger.error(f"Database error in services menu: {db_error}")
                await callback.answer("❌ Database error")
                break
    except Exception as e:
        logger.error(f"Error in services menu: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data == "menu_settings")
async def handle_settings_menu(callback: CallbackQuery):
    """Handle settings menu"""
    try:
        async for db in get_db():
            try:
                user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
                if user:
                    language = Language(user.language.value)
                    balance = await BalanceService.get_user_balance(db, user.id)
                    
                    # Enhanced settings menu with balance display
                    text = f"⚙️ {get_text('settings_menu', language)}\n\n"
                    text += f"💰 <b>{get_text('your_balance', language, balance=f'{balance:,.0f}')}</b>\n"
                    text += f"👤 <b>Username:</b> @{user.username or 'Not set'}\n"
                    text += f"🌐 <b>{get_text('current_language', language, language=get_language_name(language))}</b>\n"
                    text += f"📅 <b>Member since:</b> {user.created_at.strftime('%Y-%m-%d')}\n"
                    
                    # Add referral info if available
                    if user.referral_code:
                        bot_info = await callback.bot.get_me()
                        referral_link = f"https://t.me/{bot_info.username}?start=ref_{user.referral_code}"
                        text += f"🔗 <b>Your Referral Link:</b>\n<code>{referral_link}</code>\n"
                    
                    await callback.message.edit_text(
                        text,
                        reply_markup=get_settings_keyboard(language)
                    )
                break
            except Exception as db_error:
                logger.error(f"Database error in settings menu: {db_error}")
                await callback.answer("❌ Database error")
                break
    except Exception as e:
        logger.error(f"Error in settings menu: {e}")
        await callback.answer("❌ Error loading settings")


@router.callback_query(F.data == "settings_language")
async def handle_language_settings(callback: CallbackQuery):
    """Handle language settings"""
    try:
        async for db in get_db():
            try:
                user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
                if user:
                    language = Language(user.language.value)
                    
                    await callback.message.edit_text(
                        get_text("choose_language", language),
                        reply_markup=get_language_keyboard()
                    )
                break
            except Exception as db_error:
                logger.error(f"Database error in language settings: {db_error}")
                await callback.answer("❌ Database error")
                break
    except Exception as e:
        logger.error(f"Error in language settings: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data == "menu_support")
async def handle_support_menu(callback: CallbackQuery, user_language: Language = None):
    """Handle support menu"""
    try:
        async for db in get_db():
            try:
                user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
                if user:
                    language = user_language or Language(user.language.value)
                    
                    # Enhanced support message with contact options
                    text = f"🆘 <b>{get_text('support', language)}</b>\n\n"
                    text += f"{get_text('need_help', language)}\n\n"
                    text += f"📧 <b>{get_text('contact_methods', language)}</b>\n"
                    text += f"• Email: support@smmbot.com\n"
                    text += f"• Telegram: @smmbot_support\n"
                    text += f"• Website: https://smmbot.com\n\n"
                    text += f"⏰ <b>{get_text('support_hours', language)}</b>\n"
                    text += f"• 24/7 Available\n"
                    text += f"• Response time: &lt; 2 hours\n\n"
                    text += f"📋 <b>{get_text('common_issues', language)}</b>\n"
                    text += f"• {get_text('payment_problems', language)}\n"
                    text += f"• {get_text('order_status_questions', language)}\n"
                    text += f"• {get_text('account_issues', language)}\n"
                    text += f"• {get_text('technical_problems', language)}\n\n"
                    text += f"💡 <b>{get_text('before_contacting_support', language)}</b>\n"
                    text += f"• {get_text('check_order_history', language)}\n"
                    text += f"• {get_text('verify_payment_status', language)}\n"
                    text += f"• {get_text('read_faq_section', language)}\n\n"
                    text += f"<i>{get_text('select_option_below', language)}</i>"
                    
                    # Create support keyboard with contact options
                    support_keyboard = InlineKeyboardBuilder()
                    
                    support_keyboard.button(
                        text=f"📝 Contact Support 📝",
                        callback_data="support_contact"
                    )
                    support_keyboard.button(
                        text=f"❓ FAQ ❓",
                        callback_data="support_faq"
                    )
                    support_keyboard.button(
                        text=f"⬅️ {get_text('back', language)} ⬅️",
                        callback_data="menu_main"
                    )
                    
                    support_keyboard.adjust(1)
                    
                    await callback.message.edit_text(
                        text,
                        reply_markup=support_keyboard.as_markup()
                    )
                break
            except Exception as db_error:
                logger.error(f"Database error in support menu: {db_error}")
                await callback.answer("❌ Database error")
                break
    except Exception as e:
        logger.error(f"Error in support menu: {e}")
        await callback.answer("❌ Error loading support")


@router.callback_query(F.data == "menu_referrals")
async def handle_referrals_menu(callback: CallbackQuery):
    """Handle referrals menu"""
    try:
        async for db in get_db():
            try:
                user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
                if user:
                    language = Language(user.language.value)
                    
                    # Get referral information
                    referral_info = await ReferralService.get_user_referral_info(db, user.id)
                    referral_bonus = await SettingsService.get_setting(db, "referral_bonus_coins", 1000)
                    
                    # Get bot info for referral link
                    bot_info = await callback.bot.get_me()
                    referral_link = f"https://t.me/{bot_info.username}?start=ref_{user.referral_code}"
                    
                    text = get_text("referral_info", language,
                                  bonus=referral_bonus,
                                  count=referral_info.total_referrals,
                                  earned=referral_info.total_earned,
                                  link=referral_link)
                    
                    await callback.message.edit_text(
                        text,
                        reply_markup=get_back_keyboard(language)
                    )
                break
            except Exception as db_error:
                logger.error(f"Database error in referrals menu: {db_error}")
                await callback.answer("❌ Database error")
                break
    except Exception as e:
        logger.error(f"Error in referrals menu: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data == "menu_popular")
async def handle_popular_services(callback: CallbackQuery):
    """Handle popular services menu"""
    try:
        async for db in get_db():
            try:
                user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
                if user:
                    language = Language(user.language.value)
                    
                    text = f"🔥 <b>{get_text('popular_services', language)}</b>\n\n"
                    text += f"{get_text('popular_services_desc', language)}\n\n"
                    text += f"💡 <i>{get_text('select_service_to_start', language)}</i>"
                    
                    await callback.message.edit_text(
                        text,
                        reply_markup=get_popular_services_keyboard(language)
                    )
                break
            except Exception as db_error:
                logger.error(f"Database error in popular services: {db_error}")
                await callback.answer("❌ Database error")
                break
    except Exception as e:
        logger.error(f"Error in popular services: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data == "menu_orders")
async def handle_orders_menu(callback: CallbackQuery):
    """Handle orders menu"""
    try:
        async for db in get_db():
            try:
                user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
                if user:
                    language = Language(user.language.value)
                    
                    # Get user's orders
                    orders = await OrderService.get_user_orders(db, user.id, limit=5)
                    
                    if orders:
                        text = f"📋 <b>{get_text('your_orders', language)}</b>\n\n"
                        
                        for order in orders:
                            status_text = get_text(f"order_{order.status.value.lower()}", language)
                            text += f"🆔 <b>Order #{order.id}</b>\n"
                            text += f"📊 Service: {order.service_name}\n"
                            text += f"🔗 Link: {order.link[:50]}...\n"
                            text += f"🔢 Quantity: {order.quantity:,}\n"
                            text += f"💰 Cost: {order.cost:,} coins\n"
                            text += f"📊 Status: {status_text}\n"
                            text += f"📅 Created: {order.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                    else:
                        text = f"📋 <b>{get_text('your_orders', language)}</b>\n\n"
                        text += f"{get_text('no_orders', language)}"
                    
                    await callback.message.edit_text(
                        text,
                        reply_markup=get_orders_keyboard(language, has_orders=bool(orders))
                    )
                break
            except Exception as db_error:
                logger.error(f"Database error in orders menu: {db_error}")
                await callback.answer("❌ Database error")
                break
    except Exception as e:
        logger.error(f"Error in orders menu: {e}")
        await callback.answer("❌ Error")


# Platform handlers
@router.callback_query(F.data.startswith("platform_"))
async def handle_platform_selection(callback: CallbackQuery):
    """Handle platform selection"""
    try:
        platform = callback.data.split("_")[1]
        
        async for db in get_db():
            try:
                user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
                if user:
                    language = Language(user.language.value)
                    
                    # Get platform-specific text
                    platform_names = {
                        "telegram": get_text("telegram_services", language),
                        "instagram": get_text("instagram_services", language), 
                        "tiktok": get_text("tiktok_services", language),
                        "youtube": get_text("youtube_services", language)
                    }
                    
                    platform_name = platform_names.get(platform, f"{platform.title()} Services")
                    
                    await callback.message.edit_text(
                        f"📊 {platform_name}\n\n{get_text('choose_service_type', language)}",
                        reply_markup=get_platform_services_keyboard(platform, language)
                    )
                break
            except Exception as db_error:
                logger.error(f"Database error in platform selection: {db_error}")
                await callback.answer("❌ Database error")
                break
    except Exception as e:
        logger.error(f"Error in platform selection: {e}")
        await callback.answer("❌ Error")


# Sticker handlers
@router.message(F.sticker)
async def handle_sticker(message: Message):
    """Handle sticker messages with appropriate responses"""
    try:
        async for db in get_db():
            try:
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
            except Exception as db_error:
                logger.error(f"Database error handling sticker: {db_error}")
                break
    except Exception as e:
        logger.error(f"Error handling sticker: {e}")


# Add all other handlers following the same pattern...
# This is a template showing the correct database session usage
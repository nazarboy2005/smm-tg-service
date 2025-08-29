"""
User handlers for the Telegram bot
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
            return
        
        # Get payment method from state
        data = await state.get_data()
        payment_method = data.get("payment_method")
        
        if not payment_method:
            await message.answer("❌ Payment method not found. Please start again.", parse_mode=None)
            await state.clear()
            return
        
        async for db in get_db():
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


@router.callback_query(F.data.startswith("category_"))
async def handle_category_selection(callback: CallbackQuery):
    """Handle service category selection"""
    try:
        category_id = int(callback.data.split("_")[1])
        
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                language = Language(user.language.value)
                services = await ServiceService.get_services_by_category(db, category_id)
                
                if services:
                    await callback.message.edit_text(
                        get_text("choose_service", language),
                        reply_markup=get_services_keyboard(services, category_id, language)
                    )
                else:
                    await callback.message.edit_text(
                        "No services available in this category.",
                        reply_markup=get_back_keyboard(language, "menu_services")
                    )
            break
    except Exception as e:
        logger.error(f"Error in category selection: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data.startswith("service_"))
async def handle_service_selection(callback: CallbackQuery, state: FSMContext):
    """Handle service selection"""
    try:
        service_id = int(callback.data.split("_")[1])
        
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            service = await ServiceService.get_service_by_id(db, service_id)
            
            if user and service:
                language = Language(user.language.value)
                
                # Store service in state
                await state.update_data(service_id=service_id)
                await state.set_state(OrderStates.waiting_for_link)
                
                # Show service details and ask for link
                service_text = get_text("service_details", language,
                                      name=service.name,
                                      price=service.price_per_1000,
                                      min_qty=service.min_quantity,
                                      max_qty=service.max_quantity)
                
                await callback.message.edit_text(
                    f"{service_text}\n\n{get_text('enter_link', language)}",
                    reply_markup=get_back_keyboard(language, "menu_services")
                )
            break
    except Exception as e:
        logger.error(f"Error in service selection: {e}")
        await callback.answer("❌ Error")


@router.message(StateFilter(OrderStates.waiting_for_link))
async def handle_order_link(message: Message, state: FSMContext):
    """Handle order link input"""
    try:
        link = message.text.strip()
        
        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(link):
            async for db in get_db():
                user = await UserService.get_user_by_telegram_id(db, message.from_user.id)
                if user:
                    language = Language(user.language.value)
                    await message.answer(get_text("invalid_link", language))
                break
            return
        
        # Store link and ask for quantity
        await state.update_data(link=link)
        await state.set_state(OrderStates.waiting_for_quantity)
        
        data = await state.get_data()
        service_id = data.get("service_id")
        
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, message.from_user.id)
            service = await ServiceService.get_service_by_id(db, service_id)
            
            if user and service:
                language = Language(user.language.value)
                await message.answer(
                    get_text("enter_quantity", language, 
                           min_qty=service.min_quantity, 
                           max_qty=service.max_quantity)
                )
            break
            
    except Exception as e:
        logger.error(f"Error in order link: {e}")
        await message.answer("❌ Error processing link", parse_mode=None)


@router.message(StateFilter(OrderStates.waiting_for_quantity))
async def handle_order_quantity(message: Message, state: FSMContext):
    """Handle order quantity input"""
    try:
        # Validate quantity
        try:
            quantity = int(message.text.strip())
        except ValueError:
            async for db in get_db():
                user = await UserService.get_user_by_telegram_id(db, message.from_user.id)
                if user:
                    language = Language(user.language.value)
                    await message.answer("❌ Please enter a valid number", parse_mode=None)
                break
            return
        
        data = await state.get_data()
        service_id = data.get("service_id")
        link = data.get("link")
        
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, message.from_user.id)
            service = await ServiceService.get_service_by_id(db, service_id)
            
            if user and service:
                language = Language(user.language.value)
                
                # Validate quantity range
                if quantity < service.min_quantity or quantity > service.max_quantity:
                    await message.answer(
                        get_text("invalid_quantity", language,
                               min_qty=service.min_quantity,
                               max_qty=service.max_quantity)
                    )
                    return
                
                # Calculate cost
                cost = await ServiceService.calculate_order_cost(db, service_id, quantity)
                balance = await BalanceService.get_user_balance(db, user.id)
                
                # Check balance
                if balance < cost:
                    await message.answer(
                        get_text("insufficient_balance", language,
                               required=cost, current=balance)
                    )
                    await state.clear()
                    return
                
                # Store data and show confirmation
                await state.update_data(quantity=quantity, cost=cost)
                await state.set_state(OrderStates.confirmation)
                
                confirmation_text = get_text("order_confirmation", language,
                                           link=link,
                                           service=service.name,
                                           quantity=quantity,
                                           cost=cost)
                
                await message.answer(
                    confirmation_text,
                    reply_markup=get_order_confirmation_keyboard(language)
                )
            break
            
    except Exception as e:
        logger.error(f"Error in order quantity: {e}")
        await message.answer("❌ Error processing quantity", parse_mode=None)


@router.callback_query(F.data == "order_confirm", StateFilter(OrderStates.confirmation))
async def handle_order_confirm(callback: CallbackQuery, state: FSMContext):
    """Handle order confirmation"""
    try:
        data = await state.get_data()
        service_id = data.get("service_id")
        link = data.get("link")
        quantity = data.get("quantity")
        
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            
            if user:
                language = Language(user.language.value)
                
                # Create order
                order = await OrderService.create_order(
                    db=db,
                    user_id=user.id,
                    service_id=service_id,
                    link=link,
                    quantity=quantity
                )
                
                if order:
                    await callback.message.edit_text(
                        get_text("order_created", language,
                               order_id=order.id,
                               cost=order.charge)
                    )
                else:
                    await callback.message.edit_text(
                        get_text("order_failed", language)
                    )
                
                await state.clear()
            break
            
    except Exception as e:
        logger.error(f"Error in order confirm: {e}")
        await callback.answer("❌ Error creating order")
        await state.clear()


@router.callback_query(F.data == "order_cancel")
async def handle_order_cancel(callback: CallbackQuery, state: FSMContext):
    """Handle order cancellation"""
    try:
        await state.clear()
        
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                language = Language(user.language.value)
                await callback.message.edit_text(
                    "❌ Order cancelled",
                    reply_markup=get_main_menu_keyboard(language, user.is_admin),
                    parse_mode=None
                )
            break
    except Exception as e:
        logger.error(f"Error in order cancel: {e}")


@router.callback_query(F.data == "menu_orders")
async def handle_orders_menu(callback: CallbackQuery):
    """Handle orders menu"""
    try:
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                language = Language(user.language.value)
                orders = await OrderService.get_user_orders(db, user.id, limit=5)
                
                if orders:
                    text = get_text("your_orders", language) + "\n\n"
                    for order in orders:
                        status_text = get_text(f"order_{order.status.value}", language)
                        text += f"#{order.id} - {order.service.name} - {status_text}\n"
                    
                    await callback.message.edit_text(
                        text,
                        reply_markup=get_orders_keyboard(language, True)
                    )
                else:
                    await callback.message.edit_text(
                        get_text("no_orders", language),
                        reply_markup=get_orders_keyboard(language, False)
                    )
            break
    except Exception as e:
        logger.error(f"Error in orders menu: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data == "menu_referrals")
async def handle_referrals_menu(callback: CallbackQuery):
    """Handle referrals menu"""
    try:
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                language = Language(user.language.value)
                stats = await ReferralService.get_user_referral_stats(db, user.id)
                
                # Get bot username for referral link
                bot_info = await callback.bot.get_me()
                referral_link = await ReferralService.get_referral_link(
                    bot_info.username, user.referral_code
                )
                
                text = get_text("referral_info", language,
                              bonus=stats["bonus_per_referral"],
                              count=stats["referrals_count"],
                              earned=stats["total_earnings"],
                              link=referral_link)
                
                await callback.message.edit_text(
                    text,
                    reply_markup=get_back_keyboard(language)
                )
            break
    except Exception as e:
        logger.error(f"Error in referrals menu: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data == "menu_settings")
async def handle_settings_menu(callback: CallbackQuery):
    """Handle settings menu"""
    try:
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                language = Language(user.language.value)
                balance = await BalanceService.get_user_balance(db, user.id)
                
                # Enhanced settings menu with balance display
                text = f"⚙️ {get_text('settings_menu', language)}\n\n"
                text += f"💰 <b>Your Balance:</b> {balance:,.0f} coins\n"
                text += f"👤 <b>Username:</b> @{user.username or 'Not set'}\n"
                text += f"🌐 <b>Language:</b> {get_language_name(language)}\n"
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
    except Exception as e:
        logger.error(f"Error in settings menu: {e}")
        await callback.answer("❌ Error loading settings")


@router.callback_query(F.data == "settings_language")
async def handle_language_settings(callback: CallbackQuery):
    """Handle language settings"""
    try:
        await callback.message.edit_text(
            get_text("choose_language", Language.ENGLISH),
            reply_markup=get_language_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in language settings: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data == "menu_support")
async def handle_support_menu(callback: CallbackQuery, user_language: Language = None):
    """Handle support menu"""
    try:
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                language = user_language or Language(user.language.value)
                
                # Enhanced support message with contact options
                text = f"🆘 <b>Support Center</b>\n\n"
                text += f"Need help? We're here to assist you!\n\n"
                text += f"📧 <b>Contact Methods:</b>\n"
                text += f"• Email: support@smmbot.com\n"
                text += f"• Telegram: @smmbot_support\n"
                text += f"• Website: https://smmbot.com\n\n"
                text += f"⏰ <b>Support Hours:</b>\n"
                text += f"• 24/7 Available\n"
                text += f"• Response time: &lt; 2 hours\n\n"
                text += f"📋 <b>Common Issues:</b>\n"
                text += f"• Payment problems\n"
                text += f"• Order status questions\n"
                text += f"• Account issues\n"
                text += f"• Technical problems\n\n"
                text += f"💡 <b>Before contacting support:</b>\n"
                text += f"• Check your order history\n"
                text += f"• Verify payment status\n"
                text += f"• Read our FAQ section\n\n"
                text += f"<i>Select an option below:</i>"
                
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
    except Exception as e:
        logger.error(f"Error in support menu: {e}")
        await callback.answer("❌ Error loading support")


@router.callback_query(F.data == "balance_history")
async def handle_balance_history(callback: CallbackQuery):
    """Handle balance transaction history"""
    try:
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                language = Language(user.language.value)
                transactions = await BalanceService.get_user_transactions(db, user.id, limit=10)
                
                if transactions:
                    text = f"📊 <b>Transaction History</b>\n\n"
                    
                    for tx in transactions:
                        # Format transaction type
                        if tx.type == TransactionType.DEPOSIT:
                            icon = "💳"
                            type_text = "Deposit"
                        elif tx.type == TransactionType.ORDER_PAYMENT:
                            icon = "📋"
                            type_text = "Order Payment"
                        elif tx.type == TransactionType.REFERRAL_BONUS:
                            icon = "🎁"
                            type_text = "Referral Bonus"
                        else:
                            icon = "💰"
                            type_text = tx.type.value.title()
                        
                        # Format amount
                        amount_text = f"+{tx.amount:,.0f}" if tx.amount > 0 else f"{tx.amount:,.0f}"
                        
                        # Format date
                        date_text = tx.created_at.strftime("%Y-%m-%d %H:%M")
                        
                        text += f"{icon} <b>{type_text}</b>\n"
                        text += f"   Amount: {amount_text} coins\n"
                        if tx.usd_amount:
                            text += f"   USD: ${tx.usd_amount:.2f}\n"
                        text += f"   Date: {date_text}\n"
                        if tx.description:
                            text += f"   Note: {tx.description}\n"
                        text += "\n"
                else:
                    text = f"📊 <b>Transaction History</b>\n\n"
                    text += "No transactions yet.\n"
                    text += "Start by adding balance to see your transaction history!"
                
                await callback.message.edit_text(
                    text,
                    reply_markup=get_back_keyboard(language, "menu_balance")
                )
            break
    except Exception as e:
        logger.error(f"Error in balance history: {e}")
        await callback.answer("❌ Error loading transaction history")

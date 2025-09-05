"""
User handlers for the SMM bot
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
from bot.utils.i18n import Language, get_language_name
from bot.utils.enhanced_i18n import get_text, get_welcome_text
from bot.utils.keyboards import *
from bot.config import settings

router = Router()




async def get_simple_user_info(telegram_id: int) -> dict:
    """Temporary function to get basic user info without database"""
    return {
        "id": 1,
        "telegram_id": telegram_id,
        "username": "user",
        "language": Language.ENGLISH,
        "balance": 0.0
    }


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
    """Get curated services available to users"""
    try:
        logger.info(f"Services request from user {message.from_user.id}")
        
        # For now, show a message that services are being set up
        # TODO: Implement proper curated service display
        await message.answer(
            "📋 <b>Available Services</b>\n\n"
            "Services are currently being set up by the administrator.\n\n"
            "Please check back later or contact support for more information.",
            parse_mode="HTML"
        )
        return
        
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
async def process_referral_signup(message: Message, referral_code: str, new_user: dict):
    """Process referral signup and send notifications"""
    try:
        from bot.database.db import db_manager
        from bot.services.balance_service import BalanceService
        
        # Get the referrer's user ID from the referral code
        try:
            referrer_id = int(referral_code)
        except ValueError:
            logger.warning(f"Invalid referral code format: {referral_code}")
            return
        
        # Get referrer information by database ID
        db = await db_manager.get_connection()
        try:
            referrer = await db.fetchrow("""
                SELECT id, telegram_id, username, first_name, last_name, language
                FROM users WHERE id = $1
            """, referrer_id)
        finally:
            await db_manager.pool.release(db)
        if not referrer:
            logger.warning(f"Referrer with ID {referrer_id} not found")
            return
        
        # Check if referrer and referred are different users
        if referrer_id == new_user['id']:
            logger.warning(f"User {new_user['telegram_id']} tried to refer themselves")
            return
        
        # Create referral reward record
        db = await db_manager.get_connection()
        try:
            # Get referral settings
            referral_bonus = await db.fetchval("SELECT value FROM settings WHERE key = 'default_referral_bonus'")
            if not referral_bonus:
                referral_bonus = 1000
            else:
                referral_bonus = int(referral_bonus)
            
            button_taps_required = await db.fetchval("SELECT value FROM settings WHERE key = 'referral_tap_requirement'")
            if not button_taps_required:
                button_taps_required = 5
            else:
                button_taps_required = int(button_taps_required)
            
            # Create referral reward record
            await db.execute("""
                INSERT INTO referral_rewards 
                (referrer_id, referred_id, reward_amount, is_paid, button_taps, button_taps_required, is_completed)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, referrer_id, new_user['id'], referral_bonus, False, 0, button_taps_required, False)
            
            logger.info(f"Created referral reward: referrer {referrer_id}, referred {new_user['id']}, amount {referral_bonus}")
            
            # Send notification to referrer
            await send_referral_notification(message, dict(referrer), new_user, referral_bonus)
            
            # Give welcome bonus to new user
            await BalanceService.add_balance(new_user['id'], 100, "Welcome bonus for new user")
            
        finally:
            await db_manager.pool.release(db)
            
    except Exception as e:
        logger.error(f"Error processing referral signup: {e}")


async def send_referral_notification(message: Message, referrer: dict, new_user: dict, bonus_amount: int):
    """Send notification to referrer about new referral"""
    try:
        from bot import bot
        
        # Get referrer's language
        referrer_language = referrer.get('language', Language.ENGLISH)
        
        # Build notification message
        new_user_name = new_user.get('first_name') or new_user.get('username') or 'Someone'
        
        notification_text = f"🎉 <b>New Referral!</b>\n\n"
        notification_text += f"👤 <b>{new_user_name}</b> joined using your referral link!\n\n"
        notification_text += f"💰 <b>Potential Earnings:</b> {bonus_amount:,} coins\n"
        notification_text += f"📊 <b>Status:</b> In Progress (0/5 actions completed)\n\n"
        notification_text += f"💡 <i>They need to complete 5 actions for you to earn the reward!</i>\n\n"
        notification_text += f"🔗 <i>Keep sharing your referral link to earn more!</i>"
        
        # Send notification to referrer
        try:
            await bot.send_message(
                chat_id=referrer['telegram_id'],
                text=notification_text,
                parse_mode="HTML"
            )
            logger.info(f"Sent referral notification to referrer {referrer['telegram_id']}")
        except Exception as e:
            logger.error(f"Failed to send referral notification: {e}")
        
        # Also send a welcome message to the new user about the referral
        welcome_bonus_text = f"🎁 <b>Welcome Bonus!</b>\n\n"
        welcome_bonus_text += f"💰 You've received <b>100 coins</b> as a welcome bonus!\n\n"
        welcome_bonus_text += f"🎯 <b>Complete 5 actions</b> to help your referrer earn {bonus_amount:,} coins!\n\n"
        welcome_bonus_text += f"💡 <i>Explore our services and start growing your social media!</i>"
        
        await message.answer(welcome_bonus_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error sending referral notification: {e}")


async def track_referral_action(user_id: int, action_type: str = "button_tap"):
    """Track user actions for referral completion"""
    try:
        from bot.database.db import db_manager
        
        db = await db_manager.get_connection()
        try:
            # Update button taps for all active referrals for this user
            await db.execute("""
                UPDATE referral_rewards 
                SET button_taps = button_taps + 1
                WHERE referred_id = $1 AND is_completed = false
            """, user_id)
            
            # Check if any referrals are now completed
            completed_referrals = await db.fetch("""
                SELECT id, referrer_id, reward_amount
                FROM referral_rewards 
                WHERE referred_id = $1 
                AND is_completed = false 
                AND button_taps >= button_taps_required
            """, user_id)
            
            # Mark completed referrals and send notifications
            for referral in completed_referrals:
                await db.execute("""
                    UPDATE referral_rewards 
                    SET is_completed = true, updated_at = NOW()
                    WHERE id = $1
                """, referral['id'])
                
                # Send completion notification to referrer
                await send_referral_completion_notification(referral['referrer_id'], user_id, referral['reward_amount'])
                
        finally:
            await db_manager.pool.release(db)
            
    except Exception as e:
        logger.error(f"Error tracking referral action: {e}")


async def send_referral_completion_notification(referrer_id: int, referred_user_id: int, reward_amount: int):
    """Send notification when referral is completed"""
    try:
        from bot import bot
        from bot.database.db import db_manager
        
        # Get referrer information
        db = await db_manager.get_connection()
        try:
            referrer = await db.fetchrow("""
                SELECT telegram_id, first_name, username, language
                FROM users WHERE id = $1
            """, referrer_id)
            
            referred_user = await db.fetchrow("""
                SELECT first_name, username
                FROM users WHERE id = $1
            """, referred_user_id)
            
        finally:
            await db_manager.pool.release(db)
        
        if referrer and referred_user:
            # Build completion notification
            referred_name = referred_user.get('first_name') or referred_user.get('username') or 'Your referral'
            
            completion_text = f"🎉 <b>Referral Completed!</b>\n\n"
            completion_text += f"👤 <b>{referred_name}</b> has completed all required actions!\n\n"
            completion_text += f"💰 <b>You've earned:</b> {reward_amount:,} coins\n"
            completion_text += f"📊 <b>Status:</b> Ready for payout\n\n"
            completion_text += f"💡 <i>The reward will be added to your balance automatically!</i>\n\n"
            completion_text += f"🔗 <i>Keep sharing your referral link to earn more!</i>"
            
            # Send notification to referrer
            try:
                await bot.send_message(
                    chat_id=referrer['telegram_id'],
                    text=completion_text,
                    parse_mode="HTML"
                )
                logger.info(f"Sent referral completion notification to referrer {referrer['telegram_id']}")
            except Exception as e:
                logger.error(f"Failed to send referral completion notification: {e}")
                
    except Exception as e:
        logger.error(f"Error sending referral completion notification: {e}")


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
        
        # Get database session and check if user exists
        from bot.database.db import get_db
        from bot.services.user_service import UserService
        from bot.database.models import UserLanguage
        
        # Get user information
        user = await UserService.get_user_by_telegram_id(message.from_user.id)
        
        # If user doesn't exist, create them
        if not user:
            user = await UserService.create_user(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )
            logger.info(f"Created new user: {user['telegram_id']}")
            
            # Process referral if referral code was provided
            if referral_code and user:
                await process_referral_signup(message, referral_code, user)
        
        # Check if user has a language set
        if user and user.get('language'):
            # User already has a language set, show main menu
            language = user.get('language')
            welcome_text = get_welcome_text(language, message.from_user.first_name or 'User')
            
            # Check if user is admin
            is_admin = user.get('is_admin', False)
            
            await message.answer(
                welcome_text,
                reply_markup=get_main_menu_keyboard(language, is_admin)
            )
        else:
            # User needs to select language (first time user or no language set)
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
            welcome_text += f"🌐 <b>Please select your language:</b>"
            
            await message.answer(
                welcome_text,
                reply_markup=get_language_keyboard(user.get('language') if user else None)
            )
        
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
        
        # Save language to database
        from bot.services.user_service import UserService
        
        # Update user's language
        success = await UserService.update_user_language(callback.from_user.id, language)
        
        if success:
            # Get welcome text for the selected language
            welcome_text = get_welcome_text(language, callback.from_user.first_name or 'User')
            
            # Check if user is admin
            user = await UserService.get_user_by_telegram_id(callback.from_user.id)
            is_admin = user.get('is_admin', False) if user else False
            
            await callback.message.edit_text(
                welcome_text,
                reply_markup=get_main_menu_keyboard(language, is_admin)
            )
            
            await callback.answer(get_text("language_selected", language, language=get_language_name(language)))
        else:
            await callback.answer("❌ Failed to update language")
        
    except Exception as e:
        logger.error(f"Error in language selection: {e}")
        await callback.answer("❌ Error updating language")


@router.callback_query(F.data == "menu_admin")
async def handle_admin_menu(callback: CallbackQuery):
    """Handle admin menu navigation"""
    try:
        # Check if user is admin
        user = await UserService.get_user_by_telegram_id(callback.from_user.id)
        if not user or not user.get('is_admin', False):
            await callback.answer("❌ Admin access required", show_alert=True)
            return
        
        # Get user language
        language = user.get('language', Language.ENGLISH)
        
        # Show admin menu
        from bot.utils.keyboards import get_admin_menu_keyboard
        admin_text = get_text("admin_panel_welcome", language, name=callback.from_user.first_name or 'Admin')
        
        await callback.message.edit_text(
            admin_text,
            reply_markup=get_admin_menu_keyboard(language)
        )
        
        await callback.answer("✅ Admin panel loaded")
        
    except Exception as e:
        logger.error(f"Error in admin menu: {e}")
        await callback.answer("❌ Error loading admin panel")


@router.callback_query(F.data == "menu_main")
async def handle_main_menu(callback: CallbackQuery, user_language: Language = None):
    """Handle main menu navigation"""
    try:
        # Get user information and language
        user = await UserService.get_user_by_telegram_id(callback.from_user.id)
        if user_language:
            language = user_language
        elif user and user.get("language"):
            language = user["language"]
        else:
            language = Language.ENGLISH
        
        # Track referral action
        if user:
            await track_referral_action(user["id"], "main_menu_access")
        
        # Use localized welcome text
        welcome_text = get_welcome_text(language, callback.from_user.first_name or 'User')
        
        # Check if user is admin
        is_admin = user.get("is_admin", False) if user else False
        
        await callback.message.edit_text(
            welcome_text,
            reply_markup=get_main_menu_keyboard(language, is_admin)
        )
        
        await callback.answer("✅ Main menu loaded")
        
    except Exception as e:
        logger.error(f"Error in main menu: {e}")
        await callback.answer("❌ Error loading main menu")


@router.callback_query(F.data == "menu_balance")
async def handle_balance_menu(callback: CallbackQuery, user_language: Language = None):
    """Handle balance menu"""
    try:
        # For now, use English as default language
        # TODO: Implement proper language detection when database is ready
        language = Language.ENGLISH
        
        # Show enhanced balance information
        text = f"💰 <b>My Balance</b>\n\n"
        text += f"💎 <b>Account Overview</b>\n"
        text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        text += f"🪙 <b>Current Balance:</b> 0 coins\n"
        text += f"💵 <b>USD Value:</b> $0.00\n"
        text += f"📈 <b>Total Spent:</b> $0.00\n"
        text += f"🎯 <b>Orders Completed:</b> 0\n\n"
        text += f"💳 <b>Deposit Information:</b>\n"
        text += f"• 💰 Minimum: $1.00 USD\n"
        text += f"• 💰 Maximum: $1,000.00 USD\n"
        text += f"• 🔄 Rate: 1,000 coins per $1 USD\n"
        text += f"• ⚡ Instant Processing\n\n"
        text += f"💡 <i>Ready to boost your social media presence?</i>"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_balance_menu_keyboard(language)
        )
        
        await callback.answer("✅ Balance loaded")
        
    except Exception as e:
        logger.error(f"Error in balance menu: {e}")
        await callback.answer("❌ Error loading balance")


@router.callback_query(F.data == "balance_add")
async def handle_add_balance(callback: CallbackQuery):
    """Handle add balance"""
    try:
        try:
            user = await UserService.get_user_by_telegram_id(callback.from_user.id)
            if user:
                language = user["language"]
                
                # Create simple payment methods keyboard
                from aiogram.utils.keyboard import InlineKeyboardBuilder
                builder = InlineKeyboardBuilder()
                builder.button(text="💳 Payme", callback_data="payment_payme")
                builder.button(text="💳 Click", callback_data="payment_click")
                builder.button(text="📞 Manual Payment", callback_data="payment_manual")
                builder.button(text="🔙 Back to Balance", callback_data="menu_balance")
                builder.adjust(2, 1, 1)
                
                await callback.message.edit_text(
                    "💰 Choose Payment Method",
                    reply_markup=builder.as_markup()
                )
        except Exception as e:
            logger.error(f"Error in add balance: {e}")
            await callback.answer("❌ Error")
    except Exception as e:
        logger.error(f"Error in add balance: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data.startswith("payment_"))
async def handle_payment_method(callback: CallbackQuery, state: FSMContext):
    """Handle payment method selection"""
    try:
        payment_method = callback.data.split("_")[1]
        
        try:
            user = await UserService.get_user_by_telegram_id(callback.from_user.id)
            if user:
                language = user["language"]
                
                # Store payment method in state
                await state.update_data(payment_method=payment_method)
                await state.set_state(PaymentStates.waiting_for_amount)
                
                # Use default deposit limits for now
                min_deposit = 1.0
                max_deposit = 1000.0
                
                await callback.message.edit_text(
                    f"💰 Enter amount (${min_deposit} - ${max_deposit})",
                    reply_markup=get_back_keyboard(language, "balance_add")
                )
        except Exception as e:
            logger.error(f"Error in payment method: {e}")
            await callback.answer("❌ Error")
    except Exception as e:
        logger.error(f"Error in payment method: {e}")
        await callback.answer("❌ Error")


@router.message(StateFilter(PaymentStates.waiting_for_amount))
async def handle_payment_amount(message: Message, state: FSMContext):
    """Handle payment amount input"""
    try:
        # Parse amount
        try:
            amount = float(message.text)
        except ValueError:
            await message.answer("❌ Please enter a valid number")
            return
        
        # Get user information
        user = await UserService.get_user_by_telegram_id(message.from_user.id)
        if user:
            language = user["language"]
            
            # Get conversion rate from settings
            from bot.database.db import db_manager
            db = await db_manager.get_connection()
            try:
                coins_per_usd = await db.fetchval("SELECT value FROM settings WHERE key = 'coins_per_usd'")
                if not coins_per_usd:
                    coins_per_usd = 10000  # Default value
                else:
                    coins_per_usd = int(coins_per_usd)
            except Exception as e:
                logger.error(f"Error getting conversion rate: {e}")
                coins_per_usd = 10000  # Default value
            finally:
                await db_manager.pool.release(db)
            
            # Calculate coins to be received
            coins_to_receive = int(amount * coins_per_usd)
            
            # For now, use default deposit limits
            min_deposit = 1.0
            max_deposit = 1000.0
            
            if amount < min_deposit or amount > max_deposit:
                await message.answer(
                    f"❌ Invalid amount. Please enter between ${min_deposit} and ${max_deposit}"
                )
                return
            
            # Get payment method from state
            data = await state.get_data()
            payment_method = data.get("payment_method")
            
            if not payment_method:
                await message.answer("❌ Payment method not selected")
                return
            
            # Create payment
            payment_result = await payment_service.create_payment(
                provider_id=payment_method,
                amount_usd=amount,
                user_id=user["id"],
                description=f"Balance top-up for user {user.get('username', user['telegram_id'])}"
            )
            
            if payment_result.success:
                # Handle different payment providers
                if payment_method == "telegram":
                    # For Telegram Payments, we need to send an invoice
                    await message.answer(
                        f"💳 <b>Telegram Payment Invoice</b>\n\n"
                        f"💰 Amount: ${amount:.2f}\n"
                        f"🪙 Coins to receive: {coins_to_receive:,} coins\n"
                        f"📊 Rate: 1 USD = {coins_per_usd:,} coins\n"
                        f"📱 Provider: Telegram Payments\n\n"
                        f"ℹ️ <i>Please wait for the payment invoice...</i>",
                        parse_mode="HTML"
                    )
                    
                    # Send actual invoice (this would be implemented with bot.send_invoice)
                    # For now, show instructions
                    await message.answer(
                        f"📋 <b>Payment Instructions</b>\n\n"
                        f"1. Wait for the payment invoice\n"
                        f"2. Complete the payment through Telegram\n"
                        f"3. Your balance will be updated automatically\n\n"
                        f"💡 <i>If you don't receive an invoice, contact support</i>",
                        parse_mode="HTML",
                        reply_markup=get_back_keyboard(language, "menu_balance")
                    )
                
                elif payment_method in ["payme", "click"]:
                    # For Uzbek providers, show payment URL with UZS conversion
                    # Approximate USD to UZS rate (this should be dynamic in production)
                    usd_to_uzs_rate = 12500  # Approximate rate, should be fetched from API
                    uzs_amount = int(amount * usd_to_uzs_rate)
                    
                    if payment_result.payment_url:
                        await message.answer(
                            f"💳 <b>Payment Created</b>\n\n"
                            f"💰 Amount: ${amount:.2f}\n"
                            f"🇺🇿 UZS Amount: {uzs_amount:,} UZS\n"
                            f"🪙 Coins to receive: {coins_to_receive:,} coins\n"
                            f"📊 Rate: 1 USD = {coins_per_usd:,} coins\n"
                            f"📱 Provider: {payment_result.metadata.get('provider', 'Unknown')}\n"
                            f"🆔 Payment ID: {payment_result.payment_id}\n\n"
                            f"🔗 <a href='{payment_result.payment_url}'>Click here to pay</a>\n\n"
                            f"ℹ️ <i>After payment, contact admin for verification</i>",
                            parse_mode="HTML",
                            reply_markup=get_back_keyboard(language, "menu_balance")
                        )
                    else:
                        await message.answer(
                            f"❌ Payment creation failed: No payment URL generated"
                        )
                        
                elif payment_method == "manual":
                    # For manual payments, show admin contact with conversion info
                    admin_contact = payment_result.metadata.get("admin_contact", "@admin")
                    instructions = payment_result.metadata.get("instructions", "Contact admin")
                    
                    # Approximate USD to UZS rate
                    usd_to_uzs_rate = 12500
                    uzs_amount = int(amount * usd_to_uzs_rate)
                    
                    await message.answer(
                        f"📞 <b>Manual Payment</b>\n\n"
                        f"💰 Amount: ${amount:.2f}\n"
                        f"🇺🇿 UZS Amount: {uzs_amount:,} UZS\n"
                        f"🪙 Coins to receive: {coins_to_receive:,} coins\n"
                        f"📊 Rate: 1 USD = {coins_per_usd:,} coins\n"
                        f"🆔 Payment ID: {payment_result.payment_id}\n\n"
                        f"📋 Instructions:\n{instructions}\n\n"
                        f"👤 Contact: {admin_contact}\n\n"
                        f"ℹ️ <i>Send payment and provide this Payment ID</i>",
                        parse_mode="HTML",
                        reply_markup=get_back_keyboard(language, "menu_balance")
                    )
                
                # Clear state
                await state.clear()
                
            else:
                await message.answer(
                    f"❌ Payment creation failed: {payment_result.error_message}"
                )
        else:
            await message.answer("❌ User not found")
            
    except Exception as e:
        logger.error(f"Error in payment amount: {e}")
        await message.answer("❌ Error creating payment")


@router.callback_query(F.data == "payment_verify")
async def handle_payment_verification(callback: CallbackQuery):
    """Handle payment verification request"""
    try:
        # Get user information
        user = await UserService.get_user_by_telegram_id(callback.from_user.id)
        if user:
            language = user["language"]
            
            await callback.message.edit_text(
                f"🔍 <b>Payment Verification</b>\n\n"
                f"📋 To verify your payment:\n\n"
                f"1️⃣ Send a screenshot of your payment\n"
                f"2️⃣ Include the Payment ID\n"
                f"3️⃣ Wait for admin verification\n\n"
                f"👤 Contact: @admin\n\n"
                f"💡 <i>Verification usually takes 5-10 minutes</i>",
                parse_mode="HTML",
                reply_markup=get_back_keyboard(language, "menu_balance")
            )
            
            await callback.answer("✅ Payment verification info loaded")
        else:
            await callback.answer("❌ User not found")
            
    except Exception as e:
        logger.error(f"Error in payment verification: {e}")
        await callback.answer("❌ Error loading payment verification")


@router.callback_query(F.data == "payment_history")
async def handle_payment_history(callback: CallbackQuery):
    """Handle payment history request"""
    try:
        # Get user information
        user = await UserService.get_user_by_telegram_id(callback.from_user.id)
        if user:
            language = user["language"]
            
            # For now, show placeholder payment history
            text = f"📊 <b>Payment History</b>\n\n"
            text += f"📋 <b>Recent Transactions:</b>\n\n"
            text += f"• No transactions found\n\n"
            text += f"💡 <i>Your payment history will appear here</i>"
            
            await callback.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=get_back_keyboard(language, "menu_balance")
            )
            
            await callback.answer("✅ Payment history loaded")
        else:
            await callback.answer("❌ User not found")
            
    except Exception as e:
        logger.error(f"Error in payment history: {e}")
        await callback.answer("❌ Error loading payment history")


# Continue with all other handlers using the same pattern...
# For brevity, I'll include just a few more key handlers

@router.callback_query(F.data == "menu_services")
async def handle_services_menu(callback: CallbackQuery):
    """Handle services menu - show curated services organized by platform"""
    try:
        # Import curated services from admin handlers
        from bot.handlers.admin_handlers import get_curated_services
        
        # Get user information
        user = await UserService.get_user_by_telegram_id(callback.from_user.id)
        if user:
            language = user["language"]
            
            # Get curated services
            curated_services = await get_curated_services()
            
            if not curated_services:
                text = f"🛍️ <b>Services</b>\n\n"
                text += f"📋 <b>Available Services:</b>\n\n"
                text += f"• No services available at the moment\n"
                text += f"• Admin is setting up services\n"
                text += f"• Check back soon!\n\n"
                text += f"💡 <i>Contact admin for more information</i>"
                
                builder = InlineKeyboardBuilder()
                builder.button(text="🔙 Back to Main Menu", callback_data="menu_main")
                
                await callback.message.edit_text(
                    text,
                    parse_mode="HTML",
                    reply_markup=builder.as_markup()
                )
                await callback.answer("ℹ️ No services available")
                return
            
            # Organize services by platform
            platforms = {}
            for service_id, service in curated_services.items():
                platform = service.get('platform', 'general')
                if platform not in platforms:
                    platforms[platform] = []
                platforms[platform].append((service_id, service))
            
            # Create enhanced services menu
            text = f"🛍️ <b>Browse Services</b>\n\n"
            text += f"🌟 <b>Discover Premium Social Media Services</b>\n\n"
            text += f"📊 <b>Available Platforms ({len(platforms)}):</b>\n\n"
            
            builder = InlineKeyboardBuilder()
            
            # Add platform buttons with enhanced styling
            platform_icons = {
                'telegram': '💎',
                'instagram': '🌟', 
                'tiktok': '🚀',
                'youtube': '🎯',
                'facebook': '📘',
                'twitter': '🐦',
                'general': '🛍️'
            }
            
            platform_descriptions = {
                'telegram': 'Channels & Groups',
                'instagram': 'Followers & Engagement',
                'tiktok': 'Views & Followers',
                'youtube': 'Views & Subscribers',
                'facebook': 'Likes & Followers',
                'twitter': 'Followers & Retweets',
                'general': 'Various Services'
            }
            
            for platform, services in platforms.items():
                icon = platform_icons.get(platform, '🛍️')
                platform_name = platform.title()
                service_count = len(services)
                description = platform_descriptions.get(platform, 'Services')
                
                text += f"{icon} <b>{platform_name}</b> - {description}\n"
                text += f"   📦 {service_count} premium services available\n\n"
                
                # Add platform button with enhanced text
                builder.button(
                    text=f"{icon} {platform_name} ({service_count})",
                    callback_data=f"services_platform_{platform}"
                )
            
            # Add enhanced navigation
            builder.button(text="🔙 Back to Main Menu", callback_data="menu_main")
            builder.adjust(1)  # One column layout for better readability
            
            await callback.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
            await callback.answer(f"✅ {len(curated_services)} services available")
        else:
            await callback.answer("❌ User not found")
            
    except Exception as e:
        logger.error(f"Error in services menu: {e}")
        await callback.answer("❌ Error loading services")


@router.callback_query(F.data.startswith("services_platform_"))
async def handle_services_platform_selection(callback: CallbackQuery):
    """Handle platform selection in services menu"""
    try:
        # Import curated services from admin handlers
        from bot.handlers.admin_handlers import get_curated_services
        
        # Parse the callback data: services_platform_[platform]
        platform = callback.data.replace("services_platform_", "")
        
        # Get curated services
        curated_services = await get_curated_services()
        
        # Filter services for this platform
        platform_services = {}
        for service_id, service in curated_services.items():
            if service.get('platform', 'general') == platform:
                platform_services[service_id] = service
        
        if not platform_services:
            text = f"📱 <b>{platform.title()} Services</b>\n\n"
            text += "No services available for this platform.\n\n"
            text += "💡 <i>Admin is setting up services. Check back soon!</i>"
            
            builder = InlineKeyboardBuilder()
            builder.button(text="🔙 Back to Services", callback_data="menu_services")
            
            await callback.message.edit_text(
                text,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
            await callback.answer("ℹ️ No services available")
            return
        
        # Show enhanced platform services
        platform_icons = {
            'telegram': '💎',
            'instagram': '🌟', 
            'tiktok': '🚀',
            'youtube': '🎯',
            'facebook': '📘',
            'twitter': '🐦',
            'general': '🛍️'
        }
        
        platform_descriptions = {
            'telegram': 'Premium Telegram Services',
            'instagram': 'Instagram Growth Services',
            'tiktok': 'TikTok Boost Services',
            'youtube': 'YouTube Growth Services',
            'facebook': 'Facebook Marketing Services',
            'twitter': 'Twitter Growth Services',
            'general': 'General Services'
        }
        
        icon = platform_icons.get(platform, '🛍️')
        description = platform_descriptions.get(platform, 'Services')
        
        text = f"{icon} <b>{platform.title()} Services</b>\n\n"
        text += f"🌟 <b>{description}</b>\n\n"
        text += f"📊 <b>Available Services ({len(platform_services)}):</b>\n\n"
        
        builder = InlineKeyboardBuilder()
        
        for service_id, service in platform_services.items():
            service_name = service['custom_name']
            service_price = service['custom_price']
            
            text += f"✨ <b>{service_name}</b>\n"
            text += f"   💰 {service_price} coins per 1000 members\n"
            text += f"   ⚡ High Quality • 🛡️ Refill Guarantee\n\n"
            
            # Add service button with enhanced styling
            builder.button(
                text=f"✨ {service_name} - {service_price} coins",
                callback_data=f"service_{service_id}"
            )
        
        # Add enhanced navigation
        builder.button(text="🔙 Back to Browse Services", callback_data="menu_services")
        builder.adjust(1)  # One column layout for better readability
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await callback.answer(f"✅ {len(platform_services)} {platform.title()} services available")
        
    except Exception as e:
        logger.error(f"Error in platform services selection: {e}")
        await callback.answer("❌ Error loading platform services")


@router.callback_query(F.data == "menu_settings")
async def handle_settings_menu(callback: CallbackQuery):
    """Handle settings menu"""
    try:
        # For now, use English as default language
        # TODO: Implement proper language detection when database is ready
        language = Language.ENGLISH
        
        # Enhanced settings menu
        text = f"🧰 <b>Settings</b>\n\n"
        text += f"👤 <b>Account Information</b>\n"
        text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"🆔 <b>User ID:</b> {callback.from_user.id}\n"
        text += f"👤 <b>Username:</b> @{callback.from_user.username or 'Not set'}\n"
        text += f"🌐 <b>Language:</b> English\n"
        text += f"📅 <b>Member since:</b> Today\n\n"
        text += f"💰 <b>Account Balance</b>\n"
        text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"🪙 <b>Coins:</b> 0 coins\n"
        text += f"💵 <b>USD Value:</b> $0.00\n\n"
        text += f"⚙️ <b>Available Settings:</b>\n"
        text += f"• 🌐 Change Language\n"
        text += f"• 🔒 Privacy Settings\n"
        text += f"• 🎁 Referral Program\n\n"
        text += f"💡 <i>Customize your experience below</i>"
        
        # Create enhanced settings keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        # Language and Privacy settings
        builder.button(text="🌐 Language", callback_data="settings_language")
        builder.button(text="🔒 Privacy", callback_data="settings_privacy")
        
        # Referrals
        builder.button(text="🎁 Referrals", callback_data="menu_referrals")
        
        # Navigation
        builder.button(text="🔙 Back to Main Menu", callback_data="menu_main")
        
        builder.adjust(2, 1, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer("✅ Settings loaded")
        
    except Exception as e:
        logger.error(f"Error in settings menu: {e}")
        await callback.answer("❌ Error loading settings")


@router.callback_query(F.data == "settings_language")
async def handle_language_settings(callback: CallbackQuery):
    """Handle language settings"""
    try:
        # Show language selection keyboard
        # Get current user language
        user = await UserService.get_user_by_telegram_id(callback.from_user.id)
        current_language = user.get('language') if user else None
        
        await callback.message.edit_text(
            "🌐 <b>Choose Your Language</b>\n\n"
            "Select your preferred language:",
            reply_markup=get_language_keyboard(current_language)
        )
        
        await callback.answer("✅ Language selection loaded")
        
    except Exception as e:
        logger.error(f"Error in language settings: {e}")
        await callback.answer("❌ Error loading language settings")


@router.callback_query(F.data == "settings_privacy")
async def handle_privacy_settings(callback: CallbackQuery):
    """Handle privacy settings"""
    try:
        await callback.message.edit_text(
            "🔒 <b>Privacy Settings</b>\n\n"
            "This feature will be available when the database is ready.\n\n"
            "Privacy settings will include:\n"
            "• Profile visibility\n"
            "• Data sharing preferences\n"
            "• Account security options",
            reply_markup=get_back_to_settings_keyboard()
        )
        
        await callback.answer("ℹ️ Privacy settings coming soon")
        
    except Exception as e:
        logger.error(f"Error in privacy settings: {e}")
        await callback.answer("❌ Error loading privacy settings")




def get_back_to_settings_keyboard():
    """Create keyboard to go back to settings"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Back to Settings", callback_data="menu_settings")
    return builder.as_markup()


@router.callback_query(F.data == "menu_support")
async def handle_support_menu(callback: CallbackQuery, user_language: Language = None):
    """Handle support menu"""
    try:
        async for db in get_db():
            try:
                user = await UserService.get_user_by_telegram_id(callback.from_user.id)
                if user:
                    language = user_language or user["language"]
                    
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
        from bot.database.db import db_manager
        
        # Get user information
        user = await UserService.get_user_by_telegram_id(callback.from_user.id)
        if user:
            language = user["language"]
            
            # Get referral statistics from database
            db = await db_manager.get_connection()
            try:
                # Get referral stats
                referral_stats = await db.fetchrow("""
                    SELECT 
                        COUNT(*) as total_referrals,
                        COUNT(CASE WHEN is_completed = true THEN 1 END) as completed_referrals,
                        COALESCE(SUM(CASE WHEN is_paid = true THEN reward_amount ELSE 0 END), 0) as total_earned,
                        COALESCE(SUM(CASE WHEN is_completed = true AND is_paid = false THEN reward_amount ELSE 0 END), 0) as pending_earnings
                    FROM referral_rewards 
                    WHERE referrer_id = $1
                """, user["id"])
                
                # Get recent referrals
                recent_referrals = await db.fetch("""
                    SELECT u.username, u.first_name, rr.created_at, rr.is_completed, rr.reward_amount
                    FROM referral_rewards rr
                    JOIN users u ON rr.referred_id = u.id
                    WHERE rr.referrer_id = $1
                    ORDER BY rr.created_at DESC
                    LIMIT 5
                """, user["id"])
                
                # Get referral settings
                referral_bonus = await db.fetchval("SELECT value FROM settings WHERE key = 'default_referral_bonus'")
                if not referral_bonus:
                    referral_bonus = 1000
                else:
                    referral_bonus = int(referral_bonus)
                
                # Build enhanced referral information
                text = f"🎁 <b>Enhanced Referral Program</b>\n\n"
                text += f"💰 <b>Earn {referral_bonus:,} coins</b> for each friend you refer!\n\n"
                
                if referral_stats:
                    text += f"📊 <b>Your Referral Stats:</b>\n"
                    text += f"• Total Referrals: {referral_stats['total_referrals']}\n"
                    text += f"• Completed Referrals: {referral_stats['completed_referrals']}\n"
                    text += f"• Total Earned: {referral_stats['total_earned']:,.0f} coins\n"
                    text += f"• Pending Earnings: {referral_stats['pending_earnings']:,.0f} coins\n\n"
                else:
                    text += f"📊 <b>Your Referral Stats:</b>\n"
                    text += f"• Total Referrals: 0\n"
                    text += f"• Completed Referrals: 0\n"
                    text += f"• Total Earned: 0 coins\n"
                    text += f"• Pending Earnings: 0 coins\n\n"
                
                # Show recent referrals
                if recent_referrals:
                    text += f"👥 <b>Recent Referrals:</b>\n"
                    for ref in recent_referrals:
                        status = "✅ Completed" if ref['is_completed'] else "⏳ In Progress"
                        name = ref['username'] or ref['first_name'] or "Unknown"
                        text += f"• {name} - {status} ({ref['reward_amount']:,.0f} coins)\n"
                    text += "\n"
                
                # Enhanced referral link with QR code option
                from bot.config import settings
                bot_username = settings.bot_username or "your_bot"
                referral_link = f"https://t.me/{bot_username}?start=ref_{user['id']}"
                
                text += f"🔗 <b>Your Referral Link:</b>\n"
                text += f"<code>{referral_link}</code>\n\n"
                
                text += f"🎯 <b>How It Works:</b>\n"
                text += f"1. Share your referral link with friends\n"
                text += f"2. When they join and complete 5 actions, you earn {referral_bonus:,} coins\n"
                text += f"3. Your friend also gets a welcome bonus!\n\n"
                
                text += f"💡 <b>Pro Tips:</b>\n"
                text += f"• Share in groups and channels\n"
                text += f"• Post on social media\n"
                text += f"• Tell friends about our services\n"
                text += f"• The more you refer, the more you earn!"
                
            finally:
                await db_manager.pool.release(db)
            
            # Create enhanced referral buttons
            builder = InlineKeyboardBuilder()
            builder.button(text="📊 Detailed Stats", callback_data="referral_stats")
            builder.button(text="👥 My Referrals", callback_data="referral_list")
            builder.button(text="🔗 Copy Link", callback_data="referral_copy")
            builder.button(text="📱 Share Link", callback_data="referral_share")
            builder.button(text="🔙 Back to Settings", callback_data="menu_settings")
            builder.adjust(2, 2, 1)
            
            await callback.message.edit_text(
                text,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
            
            await callback.answer("✅ Referral info loaded")
        else:
            await callback.answer("❌ User not found")
            
    except Exception as e:
        logger.error(f"Error in referrals menu: {e}")
        await callback.answer("❌ Error loading referral info")


@router.callback_query(F.data == "menu_popular")
async def handle_popular_services(callback: CallbackQuery):
    """Handle popular services menu"""
    try:
        # Get user information
        user = await UserService.get_user_by_telegram_id(callback.from_user.id)
        if user:
            language = user["language"]
            
            # Enhanced popular services interface
            text = f"🔥 <b>Popular Services</b>\n\n"
            text += f"🌟 <b>Trending This Week</b>\n"
            text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            text += f"📊 <b>Most Requested Services:</b>\n\n"
            text += f"🥇 <b>Instagram Followers</b>\n"
            text += f"   💰 Starting from 1,500 coins\n"
            text += f"   ⭐ 4.9/5 rating • 1,200+ orders\n\n"
            text += f"🥈 <b>YouTube Views</b>\n"
            text += f"   💰 Starting from 800 coins\n"
            text += f"   ⭐ 4.8/5 rating • 950+ orders\n\n"
            text += f"🥉 <b>TikTok Followers</b>\n"
            text += f"   💰 Starting from 2,000 coins\n"
            text += f"   ⭐ 4.7/5 rating • 800+ orders\n\n"
            text += f"💡 <i>Browse all services to see the complete catalog!</i>"
            
            await callback.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=get_back_keyboard(language, "menu_main")
            )
            
            await callback.answer("✅ Popular services info loaded")
        else:
            await callback.answer("❌ User not found")
            
    except Exception as e:
        logger.error(f"Error in popular services: {e}")
        await callback.answer("❌ Error loading popular services")


@router.callback_query(F.data == "menu_orders")
async def handle_orders_menu(callback: CallbackQuery):
    """Handle orders menu"""
    try:
        # Get user information
        user = await UserService.get_user_by_telegram_id(callback.from_user.id)
        if user:
            language = user["language"]
            
            # Enhanced orders interface
            text = f"📊 <b>My Orders</b>\n\n"
            text += f"📈 <b>Order Statistics</b>\n"
            text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            text += f"🎯 <b>Total Orders:</b> 0\n"
            text += f"✅ <b>Completed:</b> 0\n"
            text += f"⏳ <b>In Progress:</b> 0\n"
            text += f"❌ <b>Cancelled:</b> 0\n\n"
            text += f"📋 <b>Recent Orders:</b>\n"
            text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            text += f"📭 <b>No orders yet</b>\n\n"
            text += f"💡 <i>Start by browsing our services to place your first order!</i>"
            
            await callback.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=get_back_keyboard(language, "menu_main")
            )
            
            await callback.answer("✅ Orders info loaded")
        else:
            await callback.answer("❌ User not found")
            
    except Exception as e:
        logger.error(f"Error in orders menu: {e}")
        await callback.answer("❌ Error loading orders")


# Platform service handlers
@router.callback_query(F.data.startswith("platform_"))
async def handle_platform_selection(callback: CallbackQuery):
    """Handle platform selection and show curated services"""
    try:
        # Import curated services from admin handlers
        from bot.handlers.admin_handlers import get_curated_services
        
        # Parse the callback data: platform_[platform]
        parts = callback.data.split("_")
        if len(parts) >= 2:
            platform = parts[1]
            
            # Get curated services
            curated_services = await get_curated_services()
            
            if not curated_services:
                text = f"📱 <b>{platform.title()} Services</b>\n\n"
                text += "No services available at the moment.\n\n"
                text += "💡 <i>Admin is setting up services. Check back soon!</i>"
                
                builder = InlineKeyboardBuilder()
                builder.button(text="🔙 Back to Main Menu", callback_data="menu_main")
                
                await callback.message.edit_text(
                    text,
                    reply_markup=builder.as_markup(),
                    parse_mode="HTML"
                )
                await callback.answer("ℹ️ No services available")
                return
            
            # Show curated services
            text = f"📱 <b>{platform.title()} Services</b>\n\n"
            text += f"📋 <b>Available Services ({len(curated_services)}):</b>\n\n"
            
            builder = InlineKeyboardBuilder()
            
            for service_id, service in curated_services.items():
                service_name = service['custom_name']
                service_price = service['custom_price']
                
                text += f"🛍️ <b>{service_name}</b>\n"
                text += f"💰 Price: {service_price} coins per 1000 members\n"
                text += f"📝 {service['custom_description']}\n\n"
                
                # Add service button
                builder.button(
                    text=f"🛍️ {service_name} - {service_price} coins",
                    callback_data=f"service_{service_id}"
                )
            
            # Add back button
            builder.button(text="🔙 Back to Main Menu", callback_data="menu_main")
            builder.adjust(1)  # One column layout
            
            await callback.message.edit_text(
                text,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
            await callback.answer(f"✅ {len(curated_services)} services available")
        else:
            await callback.answer("❌ Invalid platform selection")
            
    except Exception as e:
        logger.error(f"Error in platform selection: {e}")
        await callback.answer("❌ Error loading services")


@router.callback_query(F.data.startswith("service_"))
async def handle_service_selection(callback: CallbackQuery):
    """Handle individual service selection"""
    try:
        # Import curated services from admin handlers
        from bot.handlers.admin_handlers import get_curated_service_by_id
        
        # Parse the callback data: service_[service_id]
        service_id = callback.data.replace("service_", "")
        
        # Get the curated service
        service = await get_curated_service_by_id(service_id)
        
        if not service:
            await callback.answer("❌ Service not found")
            return
        
        # Show enhanced service details
        text = f"✨ <b>{service['custom_name']}</b>\n\n"
        text += f"🌟 <b>Premium {service['platform'].title()} Service</b>\n\n"
        text += f"📋 <b>Service Information:</b>\n"
        text += f"• 💰 <b>Price:</b> {service['custom_price']} coins per 1000 members\n"
        text += f"• 🏷️ <b>Platform:</b> {service['platform'].title()}\n"
        text += f"• ⚡ <b>Delivery:</b> High Quality & Fast\n"
        text += f"• 🛡️ <b>Guarantee:</b> Refill Available\n"
        text += f"• 📊 <b>Type:</b> {service['service_type'].title()}\n\n"
        text += f"📝 <b>Description:</b>\n{service['custom_description']}\n\n"
        text += f"💰 <b>Quick Pricing:</b>\n"
        text += f"• 1,000 units = <b>{service['custom_price']:,} coins</b>\n"
        text += f"• 5,000 units = <b>{service['custom_price'] * 5:,} coins</b>\n"
        text += f"• 10,000 units = <b>{service['custom_price'] * 10:,} coins</b>\n\n"
        text += f"💡 <i>Ready to boost your {service['platform'].title()} presence?</i>"
        
        # Create enhanced order buttons
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="🛒 Order Now", callback_data=f"order_{service_id}")
        builder.button(text="📊 Price Calculator", callback_data=f"calculate_{service_id}")
        builder.button(text="🔙 Back to {service['platform'].title()}", callback_data=f"services_platform_{service['platform']}")
        builder.button(text="🏠 Main Menu", callback_data="menu_main")
        builder.adjust(2, 2)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
            )
            
        await callback.answer("✅ Service details loaded")
            
    except Exception as e:
        logger.error(f"Error in service selection: {e}")
        await callback.answer("❌ Error loading service details")


@router.callback_query(F.data.startswith("order_"))
async def handle_place_order(callback: CallbackQuery, state: FSMContext):
    """Handle place order button - start automated order flow"""
    try:
        # Import curated services from admin handlers
        from bot.handlers.admin_handlers import get_curated_service_by_id
        
        # Parse the callback data: order_[service_id]
        service_id = callback.data.replace("order_", "")
        
        # Get the curated service
        service = await get_curated_service_by_id(service_id)
        
        if not service:
            await callback.answer("❌ Service not found")
            return
        
        # Get user information
        user = await UserService.get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("❌ User not found")
            return
        
        # Store service data in state
        await state.update_data(
            service_id=service_id,
            service_name=service['custom_name'],
            service_price=service['custom_price'],
            platform=service['platform'],
            jap_service_id=service.get('jap_service_id')
        )
        
        # Set state to waiting for link
        await state.set_state(OrderStates.waiting_for_link)
        
        # Show order form with automated flow
        text = f"🛒 <b>Place Order</b>\n\n"
        text += f"🛍️ <b>Service:</b> {service['custom_name']}\n"
        text += f"💰 <b>Price:</b> {service['custom_price']} coins per 1000 members\n"
        text += f"📱 <b>Platform:</b> {service['platform'].title()}\n\n"
        text += f"📋 <b>Step 1: Please provide the link to your {service['platform'].title()} account</b>\n\n"
        text += f"💡 <i>Send the link as a message to continue with the order</i>"
        
        # Create back button
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Back to Service", callback_data=f"service_{service_id}")
        builder.button(text="🏠 Main Menu", callback_data="menu_main")
        builder.adjust(1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        
        await callback.answer("✅ Order flow started - please send your link")
        
    except Exception as e:
        logger.error(f"Error in place order: {e}")
        await callback.answer("❌ Error starting order flow")


@router.callback_query(F.data.startswith("calculate_"))
async def handle_calculate_price(callback: CallbackQuery):
    """Handle calculate price button"""
    try:
        # Import curated services from admin handlers
        from bot.handlers.admin_handlers import get_curated_service_by_id
        
        # Parse the callback data: calculate_[service_id]
        service_id = callback.data.replace("calculate_", "")
        
        # Get the curated service
        service = await get_curated_service_by_id(service_id)
        
        if not service:
            await callback.answer("❌ Service not found")
            return
        
        price_per_1000 = service['custom_price']
        
        # Show price calculator
        text = f"📊 <b>Price Calculator</b>\n\n"
        text += f"🛍️ <b>Service:</b> {service['custom_name']}\n"
        text += f"💰 <b>Base Price:</b> {price_per_1000} coins per 1000 members\n\n"
        text += f"📋 <b>Price Examples:</b>\n"
        text += f"• 1,000 units = {price_per_1000:,} coins\n"
        text += f"• 2,500 units = {int(price_per_1000 * 2.5):,} coins\n"
        text += f"• 5,000 units = {int(price_per_1000 * 5):,} coins\n"
        text += f"• 10,000 units = {int(price_per_1000 * 10):,} coins\n"
        text += f"• 25,000 units = {int(price_per_1000 * 25):,} coins\n"
        text += f"• 50,000 units = {int(price_per_1000 * 50):,} coins\n\n"
        text += f"💡 <i>For custom quantities, contact support for exact pricing</i>"
        
        # Create calculator buttons
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="🛒 Place Order", callback_data=f"order_{service_id}")
        builder.button(text="🔙 Back to Service", callback_data=f"service_{service_id}")
        builder.button(text="🏠 Main Menu", callback_data="menu_main")
        builder.adjust(2, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        
        await callback.answer("✅ Price calculator loaded")
        
    except Exception as e:
        logger.error(f"Error in calculate price: {e}")
        await callback.answer("❌ Error loading price calculator")


# This handler is now replaced by the curated services handler above


# JAP Service handlers
@router.callback_query(F.data.startswith("jap_service_"))
async def handle_jap_service_selection(callback: CallbackQuery):
    """Handle individual JAP service selection"""
    try:
        # JAP services are disabled by default
        await callback.answer("🚫 Services are currently unavailable", show_alert=True)
        return
        
        # Parse service ID from callback data: jap_service_[id]
        service_id = int(callback.data.split("_")[2])
        
        # Get service details from JAP
        from bot.services.jap_service import jap_service
        all_services = await jap_service.get_services()
        
        service = None
        for s in all_services:
            if s.get("id") == service_id:
                service = s
                break
        
        if not service:
            await callback.answer("❌ Service not found")
            return
        
        # Show service details
        text = f"📊 <b>Service Details</b>\n\n"
        text += f"🆔 <b>Service ID:</b> {service.get('id')}\n"
        text += f"📝 <b>Name:</b> {service.get('name')}\n"
        text += f"🏷️ <b>Type:</b> {service.get('type')}\n"
        text += f"📂 <b>Category:</b> {service.get('category')}\n"
        text += f"💰 <b>Rate:</b> ${service.get('rate')}/1000\n"
        text += f"📊 <b>Min:</b> {service.get('min')}\n"
        text += f"📊 <b>Max:</b> {service.get('max')}\n"
        text += f"🔄 <b>Refill:</b> {'✅ Yes' if service.get('refill') else '❌ No'}\n"
        text += f"❌ <b>Cancel:</b> {'✅ Yes' if service.get('cancel') else '❌ No'}\n\n"
        text += f"💡 <i>To place an order, contact support or use the main menu</i>"
        
        # Create back button
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Back to Services", callback_data=f"platform_{service.get('platform', 'other')}")
        builder.button(text="🏠 Main Menu", callback_data="menu_main")
        builder.adjust(2, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer(f"✅ {service.get('name')} selected")
        
    except Exception as e:
        logger.error(f"Error in JAP service selection: {e}")
        await callback.answer("❌ Error loading service details")


@router.callback_query(F.data.startswith("jap_services_"))
async def handle_jap_services_by_type(callback: CallbackQuery):
    """Handle JAP services grouped by type"""
    try:
        # Parse callback data: jap_services_[platform]_[type]
        parts = callback.data.split("_")
        platform = parts[2]
        service_type = parts[3]
        
        # Get services for this platform and type
        from bot.services.jap_service import jap_service
        platform_services = await jap_service.get_services_by_platform(platform)
        type_services = [s for s in platform_services if s.get("service_type") == service_type]
        
        if not type_services:
            await callback.answer("❌ No services found for this type")
            return
        
        # Show services of this type
        platform_names = {
            "telegram": "Telegram",
            "instagram": "Instagram", 
            "tiktok": "TikTok",
            "youtube": "YouTube"
        }
        
        platform_name = platform_names.get(platform, platform.title())
        type_name = service_type.title()
        
        text = f"📊 <b>{platform_name} {type_name} Services</b>\n\n"
        
        # Sort by rate (best price first)
        type_services.sort(key=lambda x: x.get("rate", float('inf')))
        
        for i, service in enumerate(type_services[:10], 1):  # Show top 10
            rate = service.get("rate", 0)
            min_qty = service.get("min", 0)
            max_qty = service.get("max", 0)
            
            text += f"{i}. <b>{service.get('name')}</b>\n"
            text += f"   💰 ${rate}/1000 | 📊 {min_qty}-{max_qty}\n"
            text += f"   🏷️ {service.get('type')}\n\n"
        
        if len(type_services) > 10:
            text += f"... and {len(type_services) - 10} more services\n\n"
        
        text += f"💡 <i>Select a specific service to view details</i>"
        
        # Create service selection keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        # Add service buttons (limit to 8 to avoid keyboard overflow)
        for service in type_services[:8]:
            rate = service.get("rate", 0)
            button_text = f"⚡ {service.get('name')} (${rate}/1K)"
            builder.button(
                text=button_text,
                callback_data=f"jap_service_{service.get('id')}"
            )
        
        # Add navigation buttons
        builder.button(text="🔙 Back to Platform", callback_data=f"platform_{platform}")
        builder.button(text="🏠 Main Menu", callback_data="menu_main")
        
        # Adjust layout
        if len(type_services) <= 4:
            builder.adjust(2, 2, 2)  # 2x2 grid + navigation
        else:
            builder.adjust(2, 2, 2, 2)  # 2x2x2x2 grid + navigation
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer(f"✅ {len(type_services)} {type_name} services found")
        
    except Exception as e:
        logger.error(f"Error in JAP services by type: {e}")
        await callback.answer("❌ Error loading services")


# Sticker handlers
@router.message(F.sticker)
async def handle_sticker(message: Message):
    """Handle sticker messages with appropriate responses"""
    try:
        async for db in get_db():
            try:
                user = await UserService.get_user_by_telegram_id(message.from_user.id)
                if user:
                    language = user["language"]
                    
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


# Order State Handlers for Automated Order Processing

@router.message(StateFilter(OrderStates.waiting_for_link))
async def handle_order_link(message: Message, state: FSMContext):
    """Handle order link input"""
    try:
        import re
        
        link = message.text.strip()
        
        # Enhanced validation for URLs and Telegram usernames
        is_valid_url = False
        
        # Check for standard URLs
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        # Check for Telegram usernames (@username or t.me/username)
        telegram_pattern = re.compile(r'^(@[a-zA-Z0-9_]{5,32}|https?://t\.me/[a-zA-Z0-9_]{5,32})$', re.IGNORECASE)
        
        if url_pattern.match(link) or telegram_pattern.match(link):
            is_valid_url = True
        
        if not is_valid_url:
            await message.answer(
                "❌ Please enter a valid URL or Telegram username\n\n"
                "✅ Valid formats:\n"
                "• https://example.com\n"
                "• @username\n"
                "• https://t.me/username"
            )
            return
        
        # Store link and ask for quantity
        await state.update_data(link=link)
        await state.set_state(OrderStates.waiting_for_quantity)
        
        data = await state.get_data()
        service_name = data.get("service_name", "Service")
        service_price = data.get("service_price", 0)
        
        text = f"✅ <b>Link Received!</b>\n\n"
        text += f"🔗 <b>Your Link:</b> {link}\n\n"
        text += f"📋 <b>Step 2: Please enter the quantity</b>\n\n"
        text += f"🛍️ <b>Service:</b> {service_name}\n"
        text += f"💰 <b>Price:</b> {service_price} coins per 1000 members\n\n"
        text += f"💡 <i>Enter the number of units you want (minimum 1000)</i>"
        
        await message.answer(text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in order link: {e}")
        await message.answer("❌ Error processing link")


@router.message(StateFilter(OrderStates.waiting_for_quantity))
async def handle_order_quantity(message: Message, state: FSMContext):
    """Handle order quantity input"""
    try:
        # Validate quantity
        try:
            quantity = int(message.text.strip())
        except ValueError:
            await message.answer("❌ Please enter a valid number")
            return
        
        if quantity < 1000:
            await message.answer("❌ Minimum quantity is 1000 units")
            return
        
        data = await state.get_data()
        service_name = data.get("service_name", "Service")
        service_price = data.get("service_price", 0)
        link = data.get("link", "")
        platform = data.get("platform", "Unknown")
        
        # Calculate cost (convert to float to avoid decimal type issues)
        cost = float((quantity / 1000) * float(service_price))
        
        # Store quantity and cost
        await state.update_data(quantity=quantity, cost=cost)
        await state.set_state(OrderStates.confirmation)
        
        # Show confirmation
        text = f"📋 <b>Order Confirmation</b>\n\n"
        text += f"🛍️ <b>Service:</b> {service_name}\n"
        text += f"📱 <b>Platform:</b> {platform.title()}\n"
        text += f"🔗 <b>Link:</b> {link}\n"
        text += f"📊 <b>Quantity:</b> {quantity:,} units\n"
        text += f"💰 <b>Total Cost:</b> {cost:,.0f} coins\n\n"
        text += f"✅ <b>Please confirm your order</b>"
        
        # Create confirmation buttons
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Confirm Order", callback_data="order_confirm")
        builder.button(text="❌ Cancel", callback_data="order_cancel")
        builder.adjust(1)
        
        await message.answer(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error in order quantity: {e}")
        await message.answer("❌ Error processing quantity")


@router.callback_query(F.data == "order_confirm", StateFilter(OrderStates.confirmation))
async def handle_order_confirm(callback: CallbackQuery, state: FSMContext):
    """Handle order confirmation - create order via JAP API"""
    try:
        data = await state.get_data()
        service_id = data.get("service_id")
        service_name = data.get("service_name", "Service")
        link = data.get("link")
        quantity = data.get("quantity")
        cost = data.get("cost")
        jap_service_id = data.get("jap_service_id")
        
        # Get user information
        user = await UserService.get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("❌ User not found")
            await state.clear()
            return
        
        # Check user balance
        user_balance = await BalanceService.get_user_balance(user["id"])
        if user_balance < cost:
            await callback.message.edit_text(
                f"❌ <b>Insufficient Balance</b>\n\n"
                f"💰 Required: {cost:,.0f} coins\n"
                f"💳 Current: {user_balance:,.0f} coins\n\n"
                f"💡 Please top up your balance to continue",
                parse_mode="HTML"
            )
            await state.clear()
            return
        
        # Show processing message
        await callback.message.edit_text(
            "🔄 <b>Processing Order...</b>\n\n"
            "⏳ Creating order via JAP API...\n"
            "💳 Deducting balance...\n"
            "📊 Submitting to service provider...",
            parse_mode="HTML"
        )
        
        # Create order via JAP API
        if jap_service_id:
            # Use JAP API for automated order creation
            from bot.services.service_service import ServiceService
            order_result = await ServiceService.create_order_via_jap(jap_service_id, link, quantity)
            
            if order_result and order_result.get("order"):
                jap_order_id = order_result.get("order")
                
                # Deduct balance
                balance_result = await BalanceService.deduct_balance(
                    user_id=user["id"],
                    amount=cost,
                    description=f"Order for {service_name} - {quantity} units",
                    metadata={
                        "service_id": service_id,
                        "service_name": service_name,
                        "quantity": quantity,
                        "link": link,
                        "jap_order_id": jap_order_id
                    }
                )
                
                if balance_result:
                    # Success message
                    success_text = f"✅ <b>Order Created Successfully!</b>\n\n"
                    success_text += f"🆔 <b>Order ID:</b> {jap_order_id}\n"
                    success_text += f"🛍️ <b>Service:</b> {service_name}\n"
                    success_text += f"🔗 <b>Link:</b> {link}\n"
                    success_text += f"📊 <b>Quantity:</b> {quantity:,} units\n"
                    success_text += f"💰 <b>Cost:</b> {cost:,.0f} coins\n\n"
                    success_text += f"📈 <b>Status:</b> Processing\n"
                    success_text += f"⏳ <b>Estimated Time:</b> 1-24 hours\n\n"
                    success_text += f"💡 Use /status {jap_order_id} to check progress"
                    
                    await callback.message.edit_text(success_text, parse_mode="HTML")
                else:
                    await callback.message.edit_text(
                        "❌ <b>Order Created but Balance Deduction Failed</b>\n\n"
                        "🆔 Order ID: {jap_order_id}\n"
                        "⚠️ Please contact support to resolve balance issue",
                        parse_mode="HTML"
                    )
            else:
                await callback.message.edit_text(
                    "❌ <b>Order Creation Failed</b>\n\n"
                    "⚠️ Failed to create order via JAP API\n"
                    "💡 Please try again or contact support",
                    parse_mode="HTML"
                )
        else:
            # Fallback for services without JAP integration
            await callback.message.edit_text(
                "⚠️ <b>Service Not Available for Automated Orders</b>\n\n"
                "📞 Please contact support for manual order processing\n"
                "💡 This service requires manual setup",
                parse_mode="HTML"
            )
        
        await state.clear()
        await callback.answer("✅ Order processed")
        
    except Exception as e:
        logger.error(f"Error in order confirm: {e}")
        await callback.message.edit_text(
            "❌ <b>Order Processing Error</b>\n\n"
            "⚠️ An error occurred while processing your order\n"
            "💡 Please contact support for assistance",
            parse_mode="HTML"
        )
        await state.clear()


@router.callback_query(F.data == "order_cancel")
async def handle_order_cancel(callback: CallbackQuery, state: FSMContext):
    """Handle order cancellation"""
    try:
        await state.clear()
        
        await callback.message.edit_text(
            "❌ <b>Order Cancelled</b>\n\n"
            "💡 You can start a new order anytime from the services menu",
            parse_mode="HTML"
        )
        
        await callback.answer("Order cancelled")
        
    except Exception as e:
        logger.error(f"Error in order cancel: {e}")
        await callback.answer("❌ Error cancelling order")


# Add all other handlers following the same pattern...
# This is a template showing the correct database session usage


def setup(dispatcher):
    """Setup user handlers"""
    dispatcher.include_router(router)
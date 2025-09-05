"""
Keyboard utilities for the bot
"""
from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from bot.utils.i18n import Language, get_language_name
from bot.utils.enhanced_i18n import get_text
from bot.database.models import ServiceCategory, Service, PaymentMethod


def get_language_keyboard(current_language: Language = None) -> InlineKeyboardMarkup:
    """Create language selection keyboard with tick for current language"""
    builder = InlineKeyboardBuilder()
    
    for language in Language:
        # Add tick if this is the current language
        text = get_language_name(language)
        if current_language and language == current_language:
            text = f"✅ {text}"
        
        builder.button(
            text=text,
            callback_data=f"lang_{language.value}"
        )
    
    builder.adjust(1)
    return builder.as_markup()


def get_main_menu_keyboard(language: Language, is_admin: bool = False) -> InlineKeyboardMarkup:
    """Create premium main menu keyboard with modern social media platform styling"""
    builder = InlineKeyboardBuilder()
    
    # 🛍️ SERVICES SECTION - Main attraction
    builder.button(
        text=get_text("browse_services", language),
        callback_data="menu_services"
    )
    
    # 💰 ACCOUNT SECTION - User's financial info
    builder.button(
        text=get_text("my_balance", language),
        callback_data="menu_balance"
    )
    builder.button(
        text=get_text("my_orders", language),
        callback_data="menu_orders"
    )
    
    # 🔥 DISCOVERY SECTION - Featured content
    builder.button(
        text=get_text("popular_services", language),
        callback_data="menu_popular"
    )
    
    # ⚙️ MANAGEMENT SECTION - Settings and support
    builder.button(
        text=get_text("settings", language),
        callback_data="menu_settings"
    )
    builder.button(
        text=get_text("support", language),
        callback_data="menu_support"
    )
    
    # 👑 ADMIN SECTION - Special admin access
    if is_admin:
        builder.button(
            text=get_text("admin_panel", language),
            callback_data="menu_admin"
        )
    
    # Enhanced layout with better visual grouping
    if is_admin:
        # Services (1) | Account (2) | Discovery (1) | Management (2) | Admin (1)
        builder.adjust(1, 2, 1, 2, 1)
    else:
        # Services (1) | Account (2) | Discovery (1) | Management (2)
        builder.adjust(1, 2, 1, 2)
    
    return builder.as_markup()


def get_balance_menu_keyboard(language: Language) -> InlineKeyboardMarkup:
    """Create enhanced balance menu keyboard with payment options"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="💎 Add Balance",
        callback_data="balance_add"
    )
    builder.button(
        text="📊 Transaction History",
        callback_data="balance_history"
    )
    builder.button(
        text="🔍 Payment Verification",
        callback_data="payment_verify"
    )
    builder.button(
        text="📈 Payment History",
        callback_data="payment_history"
    )
    builder.button(
        text="🔙 Back to Main Menu",
        callback_data="menu_main"
    )
    
    # Enhanced layout for financial operations
    builder.adjust(2, 2, 1)
    return builder.as_markup()


async def get_payment_methods_keyboard(db: AsyncSession, language: Language) -> InlineKeyboardMarkup:
    """Create payment methods keyboard with simplified providers"""
    from bot.services.payment_service import payment_service
    
    builder = InlineKeyboardBuilder()
    
    # Get available payment providers
    providers = await payment_service.get_available_providers(db)
    
    # Add payment method buttons
    for provider in providers:
        provider_id = provider["id"]
        provider_name = provider["name"]
        
        builder.button(
            text=provider_name,
            callback_data=f"payment_{provider_id}"
        )
    
    # Add manual payment option (always available)
    builder.button(
        text="📞 Manual Payment",
        callback_data="payment_manual"
    )
    
    # Add back button
    builder.button(
        text=f"🔙 {get_text('back', language)}",
        callback_data="menu_balance"
    )
    
    # Layout based on number of providers
    button_count = len(providers) + 2  # +2 for manual and back
    
    if button_count > 4:
        builder.adjust(2, 2, 2, 1)  # Grid layout
    elif button_count > 2:
        builder.adjust(2, 2, 1)  # Balanced layout
    else:
        builder.adjust(2, 1)  # Compact layout
    
    return builder.as_markup()


async def get_platform_services_keyboard(platform: str, language: Language = None) -> InlineKeyboardMarkup:
    """Generate keyboard for platform services with pricing"""
    try:
        # Get services from JAP with pricing
        from bot.services.admin_service import admin_service_manager
        
        # Get services for this platform with user pricing (for_admin=False)
        services = await admin_service_manager.get_services_for_user(
            user_id=0,  # 0 means global services
            platform=platform
        )
        
        if services:
            # Group services by type
            type_services = {}
            for service in services:
                service_type = service.get("service_type", "other")
                if service_type not in type_services:
                    type_services[service_type] = []
                type_services[service_type].append(service)
            
            # Create keyboard
            builder = InlineKeyboardBuilder()
            
            # Add service type buttons
            for service_type, type_services_list in type_services.items():
                type_name = service_type.title()
                service_count = len(type_services_list)
                
                # Get average price for this type
                total_price = 0
                valid_services = 0
                for service in type_services_list:
                    if "pricing" in service:
                        price = service["pricing"].get("display_price_usd", 0)
                        if price > 0:
                            total_price += price
                            valid_services += 1
                
                avg_price = total_price / valid_services if valid_services > 0 else 0
                
                button_text = f"🏷️ {type_name}"
                if avg_price > 0:
                    button_text += f" (${avg_price:.3f}/1K)"
                button_text += f" ({service_count})"
                
                builder.button(
                    text=button_text,
                    callback_data=f"platform_service_type_{platform}_{service_type}"
                )
            
            # Add back button with language-specific text
            if language == Language.UZBEK:
                back_text = "🔙 Platformalarga Qaytish"
            else:
                back_text = "🔙 Back to Platforms"
            
            builder.button(text=back_text, callback_data="platform_selection")
            
            # Adjust layout
            if len(type_services) <= 4:
                builder.adjust(2, 2, 1)
            else:
                builder.adjust(2, 2, 2, 1)
            
            return builder.as_markup()
        
        else:
            # Fallback to static services if JAP is unavailable
            logger.warning(f"No JAP services available for {platform}, using fallback")
            return get_fallback_platform_services_keyboard(platform, language)
            
    except Exception as e:
        logger.error(f"Error getting platform services keyboard: {e}")
        # Fallback to static services
        return get_fallback_platform_services_keyboard(platform, language)


def get_fallback_platform_services_keyboard(platform: str, language: Language = None) -> InlineKeyboardMarkup:
    """Fallback keyboard when JAP services are unavailable"""
    builder = InlineKeyboardBuilder()
    
    if platform.lower() == "instagram":
        builder.button(text="🏷️ Followers (Demo)", callback_data="demo_service_instagram_followers")
        builder.button(text="🏷️ Likes (Demo)", callback_data="demo_service_instagram_likes")
        builder.button(text="🏷️ Views (Demo)", callback_data="demo_service_instagram_views")
        builder.button(text="🏷️ Comments (Demo)", callback_data="demo_service_instagram_comments")
    elif platform.lower() == "telegram":
        builder.button(text="🏷️ Members (Demo)", callback_data="demo_service_telegram_members")
        builder.button(text="🏷️ Views (Demo)", callback_data="demo_service_telegram_views")
        builder.button(text="🏷️ Reactions (Demo)", callback_data="demo_service_telegram_reactions")
    elif platform.lower() == "youtube":
        builder.button(text="🏷️ Subscribers (Demo)", callback_data="demo_service_youtube_subscribers")
        builder.button(text="🏷️ Views (Demo)", callback_data="demo_service_youtube_views")
        builder.button(text="🏷️ Likes (Demo)", callback_data="demo_service_youtube_likes")
    else:
        builder.button(text="🏷️ Followers (Demo)", callback_data="demo_service_generic_followers")
        builder.button(text="🏷️ Likes (Demo)", callback_data="demo_service_generic_likes")
        builder.button(text="🏷️ Views (Demo)", callback_data="demo_service_generic_views")
    
    # Add back button with language-specific text
    if language == Language.UZBEK:
        back_text = "🔙 Platformalarga Qaytish"
    else:
        back_text = "🔙 Back to Platforms"
    
    builder.button(text=back_text, callback_data="platform_selection")
    builder.adjust(2, 2, 1)
    
    return builder.as_markup()


def get_service_categories_keyboard(
    categories: List[ServiceCategory], 
    language: Language
) -> InlineKeyboardMarkup:
    """Create professional service categories keyboard"""
    builder = InlineKeyboardBuilder()
    
    for category in categories:
        builder.button(
            text=f"📂 {category.name}",
            callback_data=f"category_{category.id}"
        )
    
    builder.button(
        text=f"← {get_text('back', language)}",
        callback_data="menu_main"
    )
    
    builder.adjust(1)
    return builder.as_markup()


def get_services_keyboard(
    services: List[Service], 
    category_id: int,
    language: Language
) -> InlineKeyboardMarkup:
    """Create professional services keyboard"""
    builder = InlineKeyboardBuilder()
    
    for service in services:
        builder.button(
            text=f"🛍️ {service.name}",
            callback_data=f"service_{service.id}"
        )
    
    builder.button(
        text=f"← {get_text('back', language)}",
        callback_data="menu_services"
    )
    
    builder.adjust(1)
    return builder.as_markup()


def get_order_confirmation_keyboard(language: Language) -> InlineKeyboardMarkup:
    """Create professional order confirmation keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text=f"✅ {get_text('confirm', language)}",
        callback_data="order_confirm"
    )
    builder.button(
        text=f"❌ {get_text('cancel', language)}",
        callback_data="order_cancel"
    )
    
    builder.adjust(2)
    return builder.as_markup()


def get_popular_services_keyboard(language: Language) -> InlineKeyboardMarkup:
    """Create premium popular services keyboard with trending styling"""
    builder = InlineKeyboardBuilder()
    
    # Premium trending services with eye-catching icons
    builder.button(
        text=f"💎 Telegram {get_text('members', language)}",
        callback_data="popular_telegram_members"
    )
    builder.button(
        text=f"🎯 YouTube {get_text('views', language)}",
        callback_data="popular_youtube_views"
    )
    builder.button(
        text=f"🚀 TikTok {get_text('views', language)}",
        callback_data="popular_tiktok_views"
    )
    builder.button(
        text=f"🌟 Instagram {get_text('likes', language)}",
        callback_data="popular_instagram_likes"
    )
    
    builder.button(
        text=f"🔙 {get_text('back', language)}",
        callback_data="menu_main"
    )
    
    builder.adjust(2, 2, 1)  # Premium grid layout for trending services
    return builder.as_markup()


def get_orders_keyboard(language: Language, has_orders: bool = False) -> InlineKeyboardMarkup:
    """Create orders menu keyboard"""
    builder = InlineKeyboardBuilder()
    
    if has_orders:
        builder.button(
            text="📋 View Orders",
            callback_data="orders_view"
        )
    
    builder.button(
        text=get_text("back", language),
        callback_data="menu_main"
    )
    
    builder.adjust(1)
    return builder.as_markup()


def get_settings_keyboard(language: Language) -> InlineKeyboardMarkup:
    """Create professional settings keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text=f"🌐 {get_text('change_language', language)}",
        callback_data="settings_language"
    )
    builder.button(
        text="🎁 Referrals",
        callback_data="menu_referrals"
    )
    builder.button(
        text=f"← {get_text('back', language)}",
        callback_data="menu_main"
    )
    
    builder.adjust(1)
    return builder.as_markup()


def get_admin_menu_keyboard(language: Language) -> InlineKeyboardMarkup:
    """Create professional admin menu keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text=get_text('user_management', language),
        callback_data="admin_users"
    )
    builder.button(
        text=get_text('service_management', language),
        callback_data="admin_services"
    )
    builder.button(
        text=get_text('payment_management', language),
        callback_data="admin_payments"
    )
    builder.button(
        text=get_text('analytics', language),
        callback_data="admin_analytics"
    )
    builder.button(
        text=get_text('admin_settings', language),
        callback_data="admin_settings"
    )
    builder.button(
        text=get_text('back', language),
        callback_data="menu_main"
    )
    
    builder.adjust(2, 2, 2, 1)  # Professional 2-column layout for admin features
    return builder.as_markup()


def get_pagination_keyboard(
    current_page: int,
    total_pages: int,
    callback_prefix: str,
    language: Language
) -> InlineKeyboardMarkup:
    """Create pagination keyboard"""
    builder = InlineKeyboardBuilder()
    
    if current_page > 1:
        builder.button(
            text="⬅️",
            callback_data=f"{callback_prefix}_page_{current_page - 1}"
        )
    
    builder.button(
        text=f"{current_page}/{total_pages}",
        callback_data="noop"
    )
    
    if current_page < total_pages:
        builder.button(
            text="➡️",
            callback_data=f"{callback_prefix}_page_{current_page + 1}"
        )
    
    builder.button(
        text=get_text("back", language),
        callback_data="menu_main"
    )
    
    builder.adjust(3, 1)
    return builder.as_markup()


def get_yes_no_keyboard(language: Language, confirm_callback: str, cancel_callback: str) -> InlineKeyboardMarkup:
    """Create yes/no confirmation keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text=get_text("yes", language),
        callback_data=confirm_callback
    )
    builder.button(
        text=get_text("no", language),
        callback_data=cancel_callback
    )
    
    builder.adjust(2)
    return builder.as_markup()


def get_back_keyboard(language: Language, callback_data: str = "menu_main") -> InlineKeyboardMarkup:
    """Create simple back keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text=get_text("back", language),
        callback_data=callback_data
    )
    
    return builder.as_markup()

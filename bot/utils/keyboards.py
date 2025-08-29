"""
Keyboard utilities for Telegram bot inline keyboards
"""
from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.utils.i18n import get_text, Language, get_language_name
from bot.database.models import ServiceCategory, Service, PaymentMethod


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Create language selection keyboard"""
    builder = InlineKeyboardBuilder()
    
    for language in Language:
        builder.button(
            text=get_language_name(language),
            callback_data=f"lang_{language.value}"
        )
    
    builder.adjust(1)
    return builder.as_markup()


def get_main_menu_keyboard(language: Language, is_admin: bool = False) -> InlineKeyboardMarkup:
    """Create premium main menu keyboard with modern social media platform styling"""
    builder = InlineKeyboardBuilder()
    
    # Premium social media platform buttons with brand colors in mind
    builder.button(
        text=f"💎 {get_text('telegram_services', language)}",
        callback_data="platform_telegram"
    )
    builder.button(
        text=f"🌟 {get_text('instagram_services', language)}",
        callback_data="platform_instagram"
    )
    builder.button(
        text=f"🚀 {get_text('tiktok_services', language)}",
        callback_data="platform_tiktok"
    )
    builder.button(
        text=f"🎯 {get_text('youtube_services', language)}",
        callback_data="platform_youtube"
    )
    
    # Premium user account section with modern icons
    builder.button(
        text=f"💰 {get_text('balance', language)}",
        callback_data="menu_balance"
    )
    builder.button(
        text=f"📈 {get_text('orders', language)}",
        callback_data="menu_orders"
    )
    
    # Featured services with premium styling
    builder.button(
        text=f"🔥 {get_text('popular_services', language)}",
        callback_data="menu_popular"
    )
    
    # Premium additional features
    builder.button(
        text=f"🎁 {get_text('referrals', language)}",
        callback_data="menu_referrals"
    )
    builder.button(
        text=f"⚡ {get_text('settings', language)}",
        callback_data="menu_settings"
    )
    builder.button(
        text=f"🛟 {get_text('support', language)}",
        callback_data="menu_support"
    )
    
    # Premium admin menu with distinct styling
    if is_admin:
        builder.button(
            text=f"👑 {get_text('admin_menu', language)}",
            callback_data="menu_admin"
        )
    
    # Premium layout: organized grid for optimal user experience
    if is_admin:
        builder.adjust(2, 2, 1, 2, 2, 1)  # Premium layout with visual hierarchy
    else:
        builder.adjust(2, 2, 1, 2, 1)  # Clean premium layout
    
    return builder.as_markup()


def get_balance_menu_keyboard(language: Language) -> InlineKeyboardMarkup:
    """Create premium balance menu keyboard with modern financial styling"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text=f"💎 {get_text('add_balance', language)}",
        callback_data="balance_add"
    )
    builder.button(
        text=f"📈 {get_text('transaction_history', language)}",
        callback_data="balance_history"
    )
    builder.button(
        text=f"🔙 {get_text('back', language)}",
        callback_data="menu_main"
    )
    
    # Premium layout: organized for financial operations
    builder.adjust(2, 1)
    return builder.as_markup()


async def get_payment_methods_keyboard(db: AsyncSession, language: Language) -> InlineKeyboardMarkup:
    """Create premium payment methods keyboard with modern financial icons"""
    from bot.services.settings_service import SettingsService
    
    builder = InlineKeyboardBuilder()
    
    # Get enabled payment methods
    paypal_enabled = await SettingsService.get_setting(db, "paypal_enabled", True)
    crypto_enabled = await SettingsService.get_setting(db, "crypto_enabled", True)
    payme_enabled = await SettingsService.get_setting(db, "payme_enabled", True)
    click_enabled = await SettingsService.get_setting(db, "click_enabled", True)
    uzcard_enabled = await SettingsService.get_setting(db, "uzcard_enabled", False)
    humo_enabled = await SettingsService.get_setting(db, "humo_enabled", False)
    
    # Premium payment method buttons with distinctive icons
    if paypal_enabled:
        builder.button(
            text=f"🌐 {get_text('payment_paypal', language)}",
            callback_data="payment_paypal"
        )
    
    if crypto_enabled:
        builder.button(
            text=f"₿ {get_text('payment_crypto', language)}",
            callback_data="payment_crypto"
        )
    
    if payme_enabled:
        builder.button(
            text=f"📲 {get_text('payment_payme', language)}",
            callback_data="payment_payme"
        )
    
    if click_enabled:
        builder.button(
            text=f"💫 {get_text('payment_click', language)}",
            callback_data="payment_click"
        )
    
    if uzcard_enabled:
        builder.button(
            text=f"💳 {get_text('payment_uzcard', language)}",
            callback_data="payment_uzcard"
        )
    
    if humo_enabled:
        builder.button(
            text=f"🏦 {get_text('payment_humo', language)}",
            callback_data="payment_humo"
        )
    
    builder.button(
        text=f"🔙 {get_text('back', language)}",
        callback_data="menu_balance"
    )
    
    # Premium layout optimized for payment selection
    button_count = sum([paypal_enabled, crypto_enabled, payme_enabled, click_enabled, uzcard_enabled, humo_enabled])
    
    if button_count > 4:
        builder.adjust(2, 2, 2, 1)  # Premium grid layout
    elif button_count > 2:
        builder.adjust(2, 2, 1)  # Balanced layout
    else:
        builder.adjust(2, 1)  # Compact layout
    
    return builder.as_markup()


def get_platform_services_keyboard(platform: str, language: Language) -> InlineKeyboardMarkup:
    """Create premium platform-specific services keyboard with modern styling"""
    builder = InlineKeyboardBuilder()
    
    # Premium platform-specific icons that reflect service quality
    platform_icons = {
        "telegram": "💎",
        "instagram": "🌟", 
        "tiktok": "🚀",
        "youtube": "🎯",
        "twitter": "💫",
        "facebook": "🔥"
    }
    
    icon = platform_icons.get(platform.lower(), "⚡")
    
    # Premium service buttons with engaging icons
    if platform.lower() == "telegram":
        builder.button(
            text=f"{icon} {get_text('members', language)}",
            callback_data=f"platform_service_telegram_members"
        )
        builder.button(
            text=f"👁️ {get_text('views', language)}",
            callback_data=f"platform_service_telegram_views"
        )
    elif platform.lower() == "instagram":
        builder.button(
            text=f"👥 {get_text('followers', language)}",
            callback_data=f"platform_service_instagram_followers"
        )
        builder.button(
            text=f"❤️ {get_text('likes', language)}",
            callback_data=f"platform_service_instagram_likes"
        )
        builder.button(
            text=f"💬 {get_text('comments', language)}",
            callback_data=f"platform_service_instagram_comments"
        )
    elif platform.lower() == "tiktok":
        builder.button(
            text=f"👥 {get_text('followers', language)}",
            callback_data=f"platform_service_tiktok_followers"
        )
        builder.button(
            text=f"💖 {get_text('likes', language)}",
            callback_data=f"platform_service_tiktok_likes"
        )
        builder.button(
            text=f"👁️ {get_text('views', language)}",
            callback_data=f"platform_service_tiktok_views"
        )
    elif platform.lower() == "youtube":
        builder.button(
            text=f"👥 {get_text('subscribers', language)}",
            callback_data=f"platform_service_youtube_subscribers"
        )
        builder.button(
            text=f"👁️ {get_text('views', language)}",
            callback_data=f"platform_service_youtube_views"
        )
        builder.button(
            text=f"👍 {get_text('likes', language)}",
            callback_data=f"platform_service_youtube_likes"
        )
    
    builder.button(
        text=f"🔙 {get_text('back', language)}",
        callback_data="menu_main"
    )
    
    # Premium layout optimized for service selection
    if platform.lower() in ["instagram", "tiktok", "youtube"]:
        builder.adjust(2, 2, 1)  # Premium 2x2 grid + navigation
    else:
        builder.adjust(2, 1)  # Clean dual-column layout
    
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
        text=f"← {get_text('back', language)}",
        callback_data="menu_main"
    )
    
    builder.adjust(1)
    return builder.as_markup()


def get_admin_menu_keyboard(language: Language) -> InlineKeyboardMarkup:
    """Create professional admin menu keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text=f"👥 {get_text('user_management', language)}",
        callback_data="admin_users"
    )
    builder.button(
        text=f"📊 {get_text('service_management', language)}",
        callback_data="admin_services"
    )
    builder.button(
        text=f"💳 {get_text('payment_management', language)}",
        callback_data="admin_payments"
    )
    builder.button(
        text=f"📈 {get_text('analytics', language)}",
        callback_data="admin_analytics"
    )
    builder.button(
        text=f"⚙️ {get_text('settings_admin', language)}",
        callback_data="admin_settings"
    )
    builder.button(
        text=f"← {get_text('back', language)}",
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

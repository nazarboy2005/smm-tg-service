"""
Admin settings handlers for dynamic configuration management
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger

from bot.database.db import get_db
from bot.services.user_service import UserService
from bot.services.settings_service import SettingsService
from bot.utils.i18n import get_text, Language
from bot.utils.keyboards import get_back_keyboard
from bot.middleware.security_middleware import AdminOnlyMiddleware
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Create router with admin middleware
router = Router()
router.message.middleware(AdminOnlyMiddleware())
router.callback_query.middleware(AdminOnlyMiddleware())


class SettingsStates(StatesGroup):
    waiting_for_value = State()


def create_settings_keyboard(categories: dict, language: Language):
    """Create settings categories keyboard"""
    builder = InlineKeyboardBuilder()
    
    for category, settings_dict in categories.items():
        builder.button(
            text=category,
            callback_data=f"settings_cat_{hash(category) % 10000}"
        )
    
    builder.button(
        text=get_text("back", language),
        callback_data="menu_admin"
    )
    
    builder.adjust(2, 1)
    return builder.as_markup()


def create_category_settings_keyboard(category: str, settings_dict: dict, language: Language):
    """Create keyboard for settings in a category"""
    builder = InlineKeyboardBuilder()
    
    for key, setting_data in settings_dict.items():
        # Show current value in button
        current_value = setting_data["value"]
        if len(str(current_value)) > 20:
            current_value = str(current_value)[:17] + "..."
        
        button_text = f"{key.replace('_', ' ').title()}: {current_value}"
        builder.button(
            text=button_text,
            callback_data=f"setting_{key}"
        )
    
    builder.button(
        text=get_text("back", language),
        callback_data="admin_settings"
    )
    
    builder.adjust(1)
    return builder.as_markup()


def create_setting_edit_keyboard(key: str, language: Language):
    """Create keyboard for editing a specific setting"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="✏️ Change Value",
        callback_data=f"edit_{key}"
    )
    builder.button(
        text="🔄 Reset to Default",
        callback_data=f"reset_{key}"
    )
    builder.button(
        text=get_text("back", language),
        callback_data="admin_settings"
    )
    
    builder.adjust(2, 1)
    return builder.as_markup()


@router.callback_query(F.data == "admin_settings")
async def handle_admin_settings(callback: CallbackQuery):
    """Handle admin settings menu"""
    try:
        from bot.database.db import db_manager
        
        user = await UserService.get_user_by_telegram_id(callback.from_user.id)
        if user:
            language = user["language"]
            
            # Get settings by category using raw asyncpg connection
            db = await db_manager.get_connection()
            try:
                categories = await SettingsService.get_settings_by_category(db)
                
                text = f"⚙️ {get_text('settings_admin', language)}\n\n"
                text += f"{get_text('choose_category', language)}:"
                
                await callback.message.edit_text(
                    text,
                    reply_markup=create_settings_keyboard(categories, language)
                )
            finally:
                await db_manager.pool.release(db)
    except Exception as e:
        logger.error(f"Error in admin settings: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data.startswith("settings_cat_"))
async def handle_settings_category(callback: CallbackQuery):
    """Handle settings category selection"""
    try:
        from bot.database.db import db_manager
        
        user = await UserService.get_user_by_telegram_id(callback.from_user.id)
        if user:
            language = user["language"]
            
            # Get all categories to find the selected one using raw asyncpg connection
            db = await db_manager.get_connection()
            try:
                categories = await SettingsService.get_settings_by_category(db)
                
                # Find category by hash (simple approach)
                selected_category = None
                selected_settings = None
                
                for category, settings_dict in categories.items():
                    if f"settings_cat_{hash(category) % 10000}" == callback.data:
                        selected_category = category
                        selected_settings = settings_dict
                        break
                
                if selected_category and selected_settings:
                    text = f"⚙️ {selected_category}\n\n"
                    text += f"{get_text('choose_service', language)}:"
                    
                    await callback.message.edit_text(
                        text,
                        reply_markup=create_category_settings_keyboard(
                            selected_category, selected_settings, language
                        )
                    )
                else:
                    await callback.answer(f"❌ {get_text('error', language)}")
            finally:
                await db_manager.pool.release(db)
    except Exception as e:
        logger.error(f"Error in settings category: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data.startswith("setting_"))
async def handle_setting_view(callback: CallbackQuery):
    """Handle viewing a specific setting"""
    try:
        from bot.database.db import db_manager
        
        setting_key = callback.data.replace("setting_", "")
        
        user = await UserService.get_user_by_telegram_id(callback.from_user.id)
        if user:
            language = user["language"]
            
            # Get setting details using raw asyncpg connection
            db = await db_manager.get_connection()
            try:
                all_settings = await SettingsService.get_all_settings(db)
                setting_data = all_settings.get(setting_key)
                
                if setting_data:
                    text = f"⚙️ **{setting_key.replace('_', ' ').title()}**\n\n"
                    text += f"📝 Description: {setting_data['description']}\n"
                    text += f"🔧 Type: {setting_data['type']}\n"
                    text += f"💾 Current Value: `{setting_data['value']}`\n"
                    text += f"📂 Category: {setting_data['category']}\n"
                    
                    await callback.message.edit_text(
                        text,
                        reply_markup=create_setting_edit_keyboard(setting_key, language)
                    )
                else:
                    await callback.answer(f"❌ {get_text('error', language)}")
            finally:
                await db_manager.pool.release(db)
    except Exception as e:
        logger.error(f"Error viewing setting: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data.startswith("edit_"))
async def handle_setting_edit(callback: CallbackQuery, state: FSMContext):
    """Handle setting edit request"""
    try:
        setting_key = callback.data.replace("edit_", "")
        
        from bot.database.db import db_manager
        db = await db_manager.get_connection()
        try:
            user = await UserService.get_user_by_telegram_id(callback.from_user.id)
            if user:
                language = user["language"]
                
                # Get setting details
                all_settings = await SettingsService.get_all_settings(db)
                setting_data = all_settings.get(setting_key)
                
                if setting_data:
                    # Store setting key in state
                    await state.update_data(setting_key=setting_key)
                    await state.set_state(SettingsStates.waiting_for_value)
                    
                    text = f"✏️ **Edit {setting_key.replace('_', ' ').title()}**\n\n"
                    text += f"📝 Description: {setting_data['description']}\n"
                    text += f"🔧 Type: {setting_data['type']}\n"
                    text += f"💾 Current Value: `{setting_data['value']}`\n\n"
                    text += "Please enter the new value:"
                    
                    await callback.message.edit_text(
                        text,
                        reply_markup=get_back_keyboard(language, "admin_settings")
                    )
                else:
                    await callback.answer(f"❌ {get_text('error', language)}")
        finally:
            await db_manager.pool.release(db)
    except Exception as e:
        logger.error(f"Error editing setting: {e}")
        await callback.answer("❌ Error")


@router.message(StateFilter(SettingsStates.waiting_for_value))
async def handle_setting_value_input(message: Message, state: FSMContext):
    """Handle setting value input"""
    try:
        data = await state.get_data()
        setting_key = data.get("setting_key")
        new_value = message.text.strip()
        
        if not setting_key:
            # Get user language for error message
            user = await UserService.get_user_by_telegram_id(message.from_user.id)
            language = user.get("language", Language.ENGLISH) if user else Language.ENGLISH
            await message.answer(get_text("setting_key_not_found", language))
            await state.clear()
            return
        
        from bot.database.db import db_manager
        db = await db_manager.get_connection()
        try:
            user = await UserService.get_user_by_telegram_id(message.from_user.id)
            if user:
                language = user["language"]
                
                # Validate the new value
                is_valid, error_msg = await SettingsService.validate_setting_value(setting_key, new_value)
                
                if not is_valid:
                    await message.answer(f"{get_text('invalid_value', language)}: {error_msg}\n{get_text('please_try_again', language)}")
                    return
                
                # Set the new value
                success = await SettingsService.set_setting(db, setting_key, new_value, user["id"])
                
                if success:
                    await message.answer(
                        f"✅ Setting **{setting_key.replace('_', ' ').title()}** updated to: `{new_value}`"
                    )
                else:
                    await message.answer(get_text("error_updating_setting", language))
                
                await state.clear()
        finally:
            await db_manager.pool.release(db)
    except Exception as e:
        logger.error(f"Error handling setting value input: {e}")
        # Get user language for error message
        user = await UserService.get_user_by_telegram_id(message.from_user.id)
        language = user.get("language", Language.ENGLISH) if user else Language.ENGLISH
        await message.answer(get_text("error_updating_setting", language))
        await state.clear()


@router.callback_query(F.data.startswith("reset_"))
async def handle_setting_reset(callback: CallbackQuery):
    """Handle setting reset to default"""
    try:
        setting_key = callback.data.replace("reset_", "")
        
        from bot.database.db import db_manager
        db = await db_manager.get_connection()
        try:
            user = await UserService.get_user_by_telegram_id(callback.from_user.id)
            if user:
                language = user["language"]
                
                # Reset to default
                success = await SettingsService.reset_setting_to_default(db, setting_key, user["id"])
                
                if success:
                    # Get the new default value
                    default_value = SettingsService.DEFAULT_SETTINGS.get(setting_key, {}).get("value", "unknown")
                    
                    text = f"✅ Setting **{setting_key.replace('_', ' ').title()}** reset to default value: `{default_value}`"
                    
                    await callback.message.edit_text(
                        text,
                        reply_markup=get_back_keyboard(language, "admin_settings")
                    )
                else:
                    await callback.answer("❌ Failed to reset setting")
        finally:
            await db_manager.pool.release(db)
    except Exception as e:
        logger.error(f"Error resetting setting: {e}")
        await callback.answer("❌ Error")


@router.message(Command("config"))
async def cmd_config(message: Message):
    """Show current configuration"""
    try:
        from bot.database.db import db_manager
        db = await db_manager.get_connection()
        try:
            user = await UserService.get_user_by_telegram_id(message.from_user.id)
            if user and user["is_admin"]:
                # Get financial settings (most important ones)
                financial = await SettingsService.get_current_financial_settings(db)
                
                text = "⚙️ **Current Configuration**\n\n"
                text += "💰 **Financial Settings:**\n"
                text += f"• Coins per USD: {financial['coins_per_usd']}\n"
                text += f"• Min Deposit: ${financial['min_deposit_usd']}\n"
                text += f"• Max Deposit: ${financial['max_deposit_usd']}\n"
                text += f"• Referral Bonus: {financial['default_referral_bonus']} coins\n\n"
                
                # Payment methods status
                crypto_enabled = await SettingsService.get_setting(db, "crypto_enabled", True)
                payme_enabled = await SettingsService.get_setting(db, "payme_enabled", True)
                
                text += "💳 **Payment Methods:**\n"
                text += f"• Crypto: {'✅' if crypto_enabled else '❌'}\n"
                text += f"• Payme: {'✅' if payme_enabled else '❌'}\n\n"
                
                # System status
                maintenance = await SettingsService.get_setting(db, "maintenance_mode", False)
                text += f"🤖 **System Status:** {'🔧 Maintenance' if maintenance else '✅ Active'}\n"
                
                text += "\nUse /admin → Settings to modify these values."
                
                await message.answer(text)
        finally:
            await db_manager.pool.release(db)
    except Exception as e:
        logger.error(f"Error in config command: {e}")
        await message.answer(get_text("error_getting_configuration", language))


@router.message(Command("export_settings"))
async def cmd_export_settings(message: Message):
    """Export all settings as JSON"""
    try:
        from bot.database.db import db_manager
        db = await db_manager.get_connection()
        try:
            user = await UserService.get_user_by_telegram_id(message.from_user.id)
            if user and user["is_admin"]:
                settings_json = await SettingsService.export_settings(db)
                
                # Send as file
                from io import StringIO
                import datetime
                
                file_content = StringIO(settings_json)
                filename = f"bot_settings_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                await message.answer_document(
                    document=file_content,
                    filename=filename,
                    caption="📁 Bot Settings Export"
                )
        finally:
            await db_manager.pool.release(db)
    except Exception as e:
        logger.error(f"Error exporting settings: {e}")
        await message.answer(get_text("error_exporting_settings", language))


@router.message(Command("quick_config"))
async def cmd_quick_config(message: Message):
    """Quick configuration for common settings"""
    try:
        # Parse command arguments
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        
        if len(args) < 2:
            await message.answer(
                "Usage: /quick_config <setting> <value>\n\n"
                "Common settings:\n"
                "• coins_per_usd 1000\n"
                "• min_deposit_usd 1.0\n"
                "• max_deposit_usd 1000.0\n"
                "• default_referral_bonus 10\n"
                "• maintenance_mode false\n"
                "\nExample: /quick_config coins_per_usd 1200"
            )
            return
        
        setting_key = args[0]
        new_value = " ".join(args[1:])
        
        from bot.database.db import db_manager
        db = await db_manager.get_connection()
        try:
            user = await UserService.get_user_by_telegram_id(message.from_user.id)
            if user and user["is_admin"]:
                # Validate and set
                is_valid, error_msg = await SettingsService.validate_setting_value(setting_key, new_value)
                
                if not is_valid:
                    await message.answer(f"{get_text('invalid_value', language)}: {error_msg}")
                    return
                
                success = await SettingsService.set_setting(db, setting_key, new_value, user["id"])
                
                if success:
                    await message.answer(
                        f"✅ **{setting_key.replace('_', ' ').title()}** updated to: `{new_value}`"
                    )
                else:
                    await message.answer("❌ Failed to update setting")
        finally:
            await db_manager.pool.release(db)
    except Exception as e:
        logger.error(f"Error in quick config: {e}")
        await message.answer(get_text("error_updating_setting", language))


def setup(dispatcher):
    """Setup admin settings handlers"""
    dispatcher.include_router(router)

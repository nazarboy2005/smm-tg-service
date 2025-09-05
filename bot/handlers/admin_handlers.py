"""
Admin handlers for managing bot operations
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from bot.config import settings
from bot.database.db import db_manager
from bot.services.admin_service import admin_service_manager
from bot.services.jap_service import jap_service
from bot.utils.i18n import Language
from bot.utils.keyboards import get_back_keyboard

# Database-based storage for curated services
async def get_curated_services():
    """Get all active curated services from database"""
    try:
        db = await db_manager.get_connection()
        try:
            # Use raw SQL query to get curated services
            query = """
                SELECT id, jap_service_id, custom_name, custom_price_per_1000, 
                       custom_description, platform, service_type, is_active, 
                       added_by_admin_id, created_at
                FROM admin_curated_services 
                WHERE is_active = true 
                ORDER BY sort_order, custom_name
            """
            
            rows = await db.fetch(query)
            
            # Convert to dictionary format for compatibility
            result = {}
            for row in rows:
                service_id = f"curated_{row['id']}"
                result[service_id] = {
                    "id": row['id'],
                    "jap_service_id": row['jap_service_id'],
                    "custom_name": row['custom_name'],
                    "custom_price": row['custom_price_per_1000'],
                    "custom_description": row['custom_description'],
                    "platform": row['platform'] or "general",
                    "service_type": row['service_type'] or "followers",
                    "is_active": row['is_active'],
                    "added_by_admin_id": row['added_by_admin_id'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else "2025-01-01"
                }
            return result
        finally:
            # Release the connection back to the pool
            await db_manager.pool.release(db)
    except Exception as e:
        logger.error(f"Error getting curated services: {e}")
        return {}

async def get_curated_service_by_id(service_id):
    """Get a specific curated service by ID from database"""
    try:
        # Validate service_id is not a command like 'confirm'
        if not service_id or service_id in ['confirm', 'cancel', 'back']:
            logger.warning(f"Invalid service_id provided: {service_id}")
            return None
        
        # Extract numeric ID from service_id (e.g., "curated_123" -> 123)
        if service_id.startswith("curated_"):
            numeric_id = int(service_id.replace("curated_", ""))
        else:
            numeric_id = int(service_id)
        
        db = await db_manager.get_connection()
        try:
            # Use raw SQL query to get curated service by ID
            query = """
                SELECT id, jap_service_id, custom_name, custom_price_per_1000, 
                       custom_description, platform, service_type, is_active, 
                       added_by_admin_id, created_at
                FROM admin_curated_services 
                WHERE id = $1
            """
            
            row = await db.fetchrow(query, numeric_id)
            if row:
                return {
                    "id": row['id'],
                    "jap_service_id": row['jap_service_id'],
                    "custom_name": row['custom_name'],
                    "custom_price": row['custom_price_per_1000'],
                    "custom_description": row['custom_description'],
                    "platform": row['platform'] or "general",
                    "service_type": row['service_type'] or "followers",
                    "is_active": row['is_active'],
                    "added_by_admin_id": row['added_by_admin_id'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else "2025-01-01"
                }
            return None
        finally:
            # Release the connection back to the pool
            await db_manager.pool.release(db)
    except Exception as e:
        logger.error(f"Error getting curated service {service_id}: {e}")
        return None


router = Router()


@router.message(Command("enable_jap"))
async def cmd_enable_jap(message: Message):
    """Quick command to enable JAP services"""
    try:
        # For now, just show a message that JAP services are enabled
        # TODO: Implement proper admin check and settings management
        await message.answer("✅ JAP services have been enabled! (Note: This is a placeholder - proper implementation needed)")
                
    except Exception as e:
        logger.error(f"Error enabling JAP services: {e}")
        await message.answer("❌ Error enabling JAP services")


@router.message(Command("disable_jap"))
async def cmd_disable_jap(message: Message):
    """Quick command to disable JAP services"""
    try:
        # For now, just show a message that JAP services are disabled
        # TODO: Implement proper admin check and settings management
        await message.answer("✅ JAP services have been disabled! (Note: This is a placeholder - proper implementation needed)")
                
    except Exception as e:
        logger.error(f"Error disabling JAP services: {e}")
        await message.answer("❌ Error disabling JAP services")


# Curated Service Management Commands
@router.message(Command("add_service"))
async def cmd_add_service(message: Message, state: FSMContext):
    """Add a new curated service using command format"""
    try:
        # Parse command arguments: /add_service <jap_service_id> <custom_name> <price_per_1000>
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        
        if len(args) < 3:
            await message.answer(
                "📋 <b>Usage:</b> /add_service <jap_service_id> <custom_name> <price_per_1000>\n\n"
                "📝 <b>Example:</b> /add_service 1234 \"Instagram Followers Premium\" 1500\n\n"
                "💡 <i>This will add JAP service ID 1234 with custom name and price of 1500 coins per 1000 members.</i>\n\n"
                "🔄 <b>Alternative:</b> Use the interactive menu: Admin Menu → Service Management → Add Curated Service",
                parse_mode="HTML"
            )
            return
        
        try:
            jap_service_id = int(args[0])
            custom_name = args[1].strip('"')
            custom_price = float(args[2])
        except ValueError:
            await message.answer("❌ Invalid arguments. Please check the format.")
            return
        
        # Store the curated service
        service_id = f"curated_{jap_service_id}"
        curated_services[service_id] = {
            "jap_service_id": jap_service_id,
            "custom_name": custom_name,
            "custom_price": custom_price,
            "custom_description": f"Premium {custom_name} service with high quality delivery",
            "platform": "general",  # Default platform
            "service_type": "followers",  # Default type
            "is_active": True,
            "added_by_admin_id": message.from_user.id,
            "created_at": "2025-01-01"  # Placeholder date
        }
        
        await message.answer(
            f"✅ <b>Service Added Successfully!</b>\n\n"
            f"📋 <b>Service Details:</b>\n"
            f"• JAP Service ID: <b>{jap_service_id}</b>\n"
            f"• Custom Name: <b>{custom_name}</b>\n"
            f"• Price: <b>{custom_price}</b> coins per 1000 members\n"
            f"• Service ID: <b>{service_id}</b>\n\n"
            f"💡 <i>This service is now available to users!</i>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error adding service: {e}")
        await message.answer("❌ Error adding service")


@router.message(Command("list_services"))
async def cmd_list_services(message: Message):
    """List all curated services"""
    try:
        # For now, show a placeholder message
        # TODO: Implement proper database operations
        await message.answer(
            "📋 <b>Curated Services</b>\n\n"
            "No services added yet.\n\n"
            "Use /add_service to add new services.\n\n"
            "<i>Note: This is a placeholder - proper implementation needed</i>"
        )
        
    except Exception as e:
        logger.error(f"Error listing services: {e}")
        await message.answer("❌ Error listing services")


@router.message(Command("remove_service"))
async def cmd_remove_service(message: Message):
    """Remove a curated service"""
    try:
        # Parse command arguments: /remove_service <service_id>
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        
        if len(args) < 1:
            await message.answer(
                "Usage: /remove_service <service_id>\n\n"
                "Example: /remove_service 1\n\n"
                "This will remove the curated service with ID 1."
            )
            return
        
        try:
            service_id = int(args[0])
        except ValueError:
            await message.answer("❌ Invalid service ID. Please provide a number.")
            return
        
        # For now, show a placeholder message
        # TODO: Implement proper database operations
        await message.answer(
            f"✅ Service {service_id} removed successfully!\n\n"
            f"<i>Note: This is a placeholder - proper implementation needed</i>"
        )
        
    except Exception as e:
        logger.error(f"Error removing service: {e}")
        await message.answer("❌ Error removing service")

# Admin service management states
class ServiceManagementStates(StatesGroup):
    waiting_for_service_id = State()
    waiting_for_service_type = State()
    waiting_for_platform = State()
    waiting_for_user_id = State()
    waiting_for_access_level = State()
    waiting_for_global_setting = State()
    waiting_for_custom_price = State()
    waiting_for_markup = State()
    waiting_for_service_code = State()
    # Curated service states
    waiting_for_jap_service_id = State()
    waiting_for_custom_name = State()
    waiting_for_custom_price = State()
    waiting_for_custom_description = State()
    waiting_for_platform = State()
    draft_ready = State()  # Service is ready but not published


# Admin service management menu
@router.callback_query(F.data == "admin_service_management")
async def handle_admin_service_management(callback: CallbackQuery):
    """Show admin service management menu"""
    try:
        # Check if user is admin
        if callback.from_user.id not in settings.admin_ids:
            await callback.answer("❌ Access denied")
            return
        
        # Get service statistics
        stats = await admin_service_manager.get_service_statistics()
        
        text = "🔧 <b>Admin Service Management</b>\n\n"
        text += f"📊 <b>Service Statistics:</b>\n"
        text += f"• Total Services: {stats.get('total_services', 0)}\n"
        text += f"• Active Services: {stats.get('active_services', 0)}\n"
        
        if "services_by_platform" in stats:
            text += f"\n🌐 <b>Services by Platform:</b>\n"
            for platform, count in stats["services_by_platform"].items():
                text += f"• {platform.title()}: {count}\n"
        
        if "services_by_type" in stats:
            text += f"\n🏷️ <b>Services by Type:</b>\n"
            for service_type, count in stats["services_by_type"].items():
                text += f"• {service_type.title()}: {count}\n"
        
        text += "\n💡 <i>Select an option to manage services</i>"
        
        # Create service management keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        builder.button(text="🔧 Manage Service Availability", callback_data="admin_manage_service_availability")
        builder.button(text="💰 Pricing Management", callback_data="admin_pricing_management")
        builder.button(text="➕ Add New Service", callback_data="admin_add_service")
        builder.button(text="⏳ Pending Approvals", callback_data="admin_pending_services")
        builder.button(text="👥 Manage User Access", callback_data="admin_manage_user_access")
        builder.button(text="📊 Service Statistics", callback_data="admin_service_statistics")
        builder.button(text="⚙️ Service Settings", callback_data="admin_service_settings")
        
        builder.adjust(2, 2, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer("✅ Service management loaded")
        
    except Exception as e:
        logger.error(f"Error in admin service management: {e}")
        await callback.answer("❌ Error loading service management")


# Service availability management
@router.callback_query(F.data == "admin_manage_service_availability")
async def handle_manage_service_availability(callback: CallbackQuery):
    """Show service availability management options"""
    try:
        text = "🔧 <b>Service Availability Management</b>\n\n"
        text += "📋 <b>Available Actions:</b>\n"
        text += "• Enable/Disable specific services\n"
        text += "• Enable/Disable service types (followers, likes, etc.)\n"
        text += "• Enable/Disable entire platforms\n"
        text += "• Apply changes globally or per user\n\n"
        text += "💡 <i>Select an option below</i>"
        
        # Create keyboard for service availability management
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        builder.button(text="🔧 Manage Individual Services", callback_data="admin_manage_individual_services")
        builder.button(text="🏷️ Manage Service Types", callback_data="admin_manage_service_types")
        builder.button(text="🌐 Manage Platforms", callback_data="admin_manage_platforms")
        builder.button(text="👥 Manage User Access", callback_data="admin_manage_user_access")
        builder.button(text="🔙 Back to Service Management", callback_data="admin_service_management")
        
        builder.adjust(2, 2, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer("✅ Service availability options loaded")
        
    except Exception as e:
        logger.error(f"Error in service availability management: {e}")
        await callback.answer("❌ Error loading options")


# Individual service management
@router.callback_query(F.data == "admin_manage_individual_services")
async def handle_manage_individual_services(callback: CallbackQuery):
    """Show individual service management"""
    try:
        # Show curated service management instead
        text = "🔧 <b>Curated Service Management</b>\n\n"
        text += "📋 <b>Available Actions:</b>\n"
        text += "• Add new curated service\n"
        text += "• List all curated services\n"
        text += "• Edit service details\n"
        text += "• Remove services\n"
        text += "• Enable/Disable services\n\n"
        text += "💡 <i>Use the commands below or select an option</i>"
        
        # Create keyboard for curated service management
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        builder.button(text="➕ Add New Service", callback_data="admin_add_curated_service")
        builder.button(text="📋 List Services", callback_data="admin_list_curated_services")
        builder.button(text="✏️ Edit Service", callback_data="admin_edit_curated_service")
        builder.button(text="🗑️ Remove Service", callback_data="admin_remove_curated_service")
        builder.button(text="🔙 Back to Service Management", callback_data="admin_manage_service_availability")
        
        builder.adjust(2, 2, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer("✅ Curated service management loaded")
        
    except Exception as e:
        logger.error(f"Error in curated service management: {e}")
        await callback.answer("❌ Error loading service management")


# Curated Service Management Callback Handlers
@router.callback_query(F.data == "admin_add_curated_service")
async def handle_add_curated_service(callback: CallbackQuery, state: FSMContext):
    """Start the process of adding a curated service"""
    try:
        text = "➕ <b>Add New Curated Service</b>\n\n"
        text += "📋 <b>Step 1 of 5: Enter JAP Service ID</b>\n\n"
        text += "Please send the JAP service ID you want to add.\n\n"
        text += "💡 <i>You can find JAP service IDs from the JAP panel or API</i>\n\n"
        text += "📝 <b>Example:</b> 1234"
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Back to Service Management", callback_data="admin_manage_individual_services")
        builder.button(text="❌ Cancel", callback_data="admin_cancel_add_service")
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        
        # Set state to wait for JAP service ID
        await state.set_state(ServiceManagementStates.waiting_for_jap_service_id)
        await callback.answer("✅ Please send the JAP service ID")
        
    except Exception as e:
        logger.error(f"Error in add curated service: {e}")
        await callback.answer("❌ Error loading add service form")


@router.message(ServiceManagementStates.waiting_for_jap_service_id)
async def handle_jap_service_id_input(message: Message, state: FSMContext):
    """Handle JAP service ID input"""
    try:
        # Validate the service ID
        try:
            jap_service_id = int(message.text.strip())
            if jap_service_id <= 0:
                raise ValueError("Service ID must be positive")
        except ValueError:
            await message.answer("❌ Please enter a valid JAP service ID (positive number)")
            return
        
        # Store the service ID and ask for custom name
        await state.update_data(jap_service_id=jap_service_id)
        
        text = f"✅ JAP Service ID: <b>{jap_service_id}</b>\n\n"
        text += "📋 <b>Step 2 of 5: Enter Custom Name</b>\n\n"
        text += "Please send the custom name for this service.\n\n"
        text += "💡 <i>This will be the name users see in the bot</i>\n\n"
        text += "📝 <b>Example:</b> Instagram Followers Premium"
        
        # Create back button
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Back to Step 1", callback_data="admin_back_to_jap_id")
        builder.button(text="❌ Cancel", callback_data="admin_cancel_add_service")
        
        await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
        await state.set_state(ServiceManagementStates.waiting_for_custom_name)
        
    except Exception as e:
        logger.error(f"Error handling JAP service ID input: {e}")
        await message.answer("❌ Error processing service ID")


@router.message(ServiceManagementStates.waiting_for_custom_name)
async def handle_custom_name_input(message: Message, state: FSMContext):
    """Handle custom name input"""
    try:
        custom_name = message.text.strip()
        if len(custom_name) < 3:
            await message.answer("❌ Custom name must be at least 3 characters long")
            return
        
        # Store the custom name and ask for platform
        await state.update_data(custom_name=custom_name)
        
        data = await state.get_data()
        jap_service_id = data.get('jap_service_id')
        
        text = f"✅ JAP Service ID: <b>{jap_service_id}</b>\n"
        text += f"✅ Custom Name: <b>{custom_name}</b>\n\n"
        text += "📋 <b>Step 3 of 5: Select Platform</b>\n\n"
        text += "Please select the platform for this service:\n\n"
        text += "💎 Telegram\n"
        text += "🌟 Instagram\n"
        text += "🚀 TikTok\n"
        text += "🎯 YouTube\n"
        text += "📘 Facebook\n"
        text += "🐦 Twitter\n"
        text += "🛍️ General\n\n"
        text += "💡 <i>Send the platform name (e.g., 'telegram', 'instagram')</i>\n\n"
        text += "📝 <b>Example:</b> instagram"
        
        # Create back button
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Back to Step 2", callback_data="admin_back_to_custom_name")
        builder.button(text="❌ Cancel", callback_data="admin_cancel_add_service")
        
        await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
        await state.set_state(ServiceManagementStates.waiting_for_platform)
        
    except Exception as e:
        logger.error(f"Error handling custom name input: {e}")
        await message.answer("❌ Error processing custom name")


@router.message(ServiceManagementStates.waiting_for_platform)
async def handle_platform_input(message: Message, state: FSMContext):
    """Handle platform input"""
    try:
        platform = message.text.strip().lower()
        
        # Validate platform
        valid_platforms = ['telegram', 'instagram', 'tiktok', 'youtube', 'facebook', 'twitter', 'general']
        if platform not in valid_platforms:
            await message.answer("❌ Invalid platform. Please choose from: telegram, instagram, tiktok, youtube, facebook, twitter, or general")
            return
        
        # Store the platform and ask for price
        await state.update_data(platform=platform)
        
        data = await state.get_data()
        jap_service_id = data.get('jap_service_id')
        custom_name = data.get('custom_name')
        
        text = f"✅ JAP Service ID: <b>{jap_service_id}</b>\n"
        text += f"✅ Custom Name: <b>{custom_name}</b>\n"
        text += f"✅ Platform: <b>{platform.title()}</b>\n\n"
        text += "📋 <b>Step 4 of 5: Enter Price per 1000 members</b>\n\n"
        text += "Please send the price in coins per 1000 members.\n\n"
        text += "💡 <i>This is the price users will pay per 1000 members</i>\n\n"
        text += "📝 <b>Example:</b> 1500"
        
        # Create back button
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Back to Step 3", callback_data="admin_back_to_platform")
        builder.button(text="❌ Cancel", callback_data="admin_cancel_add_service")
        
        await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
        await state.set_state(ServiceManagementStates.waiting_for_custom_price)
        
    except Exception as e:
        logger.error(f"Error handling platform input: {e}")
        await message.answer("❌ Error processing platform")


@router.message(ServiceManagementStates.waiting_for_custom_price)
async def handle_custom_price_input(message: Message, state: FSMContext):
    """Handle custom price input"""
    try:
        # Validate the price
        try:
            custom_price = float(message.text.strip())
            if custom_price <= 0:
                raise ValueError("Price must be positive")
        except ValueError:
            await message.answer("❌ Please enter a valid price (positive number)")
            return
        
        # Store the price and ask for description
        await state.update_data(custom_price=custom_price)
        
        data = await state.get_data()
        jap_service_id = data.get('jap_service_id')
        custom_name = data.get('custom_name')
        platform = data.get('platform', 'general')
        
        text = f"✅ JAP Service ID: <b>{jap_service_id}</b>\n"
        text += f"✅ Custom Name: <b>{custom_name}</b>\n"
        text += f"✅ Platform: <b>{platform.title()}</b>\n"
        text += f"✅ Price: <b>{custom_price} coins per 1000 members</b>\n\n"
        text += "📋 <b>Step 5 of 5: Enter Description</b>\n\n"
        text += "Please send a description for this service.\n\n"
        text += "💡 <i>This description will be shown to users</i>\n\n"
        text += "📝 <b>Example:</b> High quality Instagram followers with instant delivery and refill guarantee"
        
        # Create back button
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Back to Step 4", callback_data="admin_back_to_price")
        builder.button(text="❌ Cancel", callback_data="admin_cancel_add_service")
        
        await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
        await state.set_state(ServiceManagementStates.waiting_for_custom_description)
        
    except Exception as e:
        logger.error(f"Error handling custom price input: {e}")
        await message.answer("❌ Error processing price")


@router.message(ServiceManagementStates.waiting_for_custom_description)
async def handle_custom_description_input(message: Message, state: FSMContext):
    """Handle custom description input and show publish confirmation"""
    try:
        custom_description = message.text.strip()
        if len(custom_description) < 10:
            await message.answer("❌ Description must be at least 10 characters long")
            return
        
        # Store the description
        await state.update_data(custom_description=custom_description)
        
        # Get all data for review
        data = await state.get_data()
        jap_service_id = data.get('jap_service_id')
        custom_name = data.get('custom_name')
        platform = data.get('platform', 'general')
        custom_price = data.get('custom_price')
        
        # Show review and publish confirmation
        text = f"📋 <b>Review Service Details</b>\n\n"
        text += f"✅ <b>JAP Service ID:</b> {jap_service_id}\n"
        text += f"✅ <b>Custom Name:</b> {custom_name}\n"
        text += f"✅ <b>Platform:</b> {platform.title()}\n"
        text += f"✅ <b>Price:</b> {custom_price} coins per 1000 members\n"
        text += f"✅ <b>Description:</b> {custom_description}\n\n"
        text += f"🤔 <b>Ready to publish this service?</b>\n\n"
        text += f"💡 <i>Once published, this service will be available to users</i>"
        
        # Create publish confirmation buttons
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Publish Service", callback_data="admin_publish_service")
        builder.button(text="🔙 Back to Description", callback_data="admin_back_to_description")
        builder.button(text="❌ Cancel", callback_data="admin_cancel_add_service")
        
        await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
        
    except Exception as e:
        logger.error(f"Error handling custom description input: {e}")
        await message.answer("❌ Error processing description")


@router.callback_query(F.data == "admin_publish_service")
async def handle_publish_service(callback: CallbackQuery, state: FSMContext):
    """Publish the curated service to database"""
    try:
        # Get all data
        data = await state.get_data()
        jap_service_id = data.get('jap_service_id')
        custom_name = data.get('custom_name')
        platform = data.get('platform', 'general')
        custom_price = data.get('custom_price')
        custom_description = data.get('custom_description')
        
        # Debug logging
        logger.info(f"Service publishing data: {data}")
        logger.info(f"JAP Service ID: {jap_service_id}, Custom Name: {custom_name}")
        
        # Validate required fields
        if not jap_service_id:
            await callback.message.edit_text(
                "❌ <b>Missing JAP Service ID</b>\n\n"
                "⚠️ Cannot publish service without JAP Service ID\n"
                "💡 Please start over and select a service from JAP",
                parse_mode="HTML"
            )
            await state.clear()
            return
            
        if not custom_name:
            await callback.message.edit_text(
                "❌ <b>Missing Custom Name</b>\n\n"
                "⚠️ Cannot publish service without custom name\n"
                "💡 Please start over and provide a custom name",
                parse_mode="HTML"
            )
            await state.clear()
            return
        
        # Save to database using raw SQL
        db = await db_manager.get_connection()
        try:
            # Insert the curated service
            insert_query = """
                INSERT INTO admin_curated_services 
                (jap_service_id, custom_name, custom_description, custom_price_per_1000, 
                 platform, service_type, is_active, added_by_admin_id, sort_order)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
            """
            
            service_id = await db.fetchval(
                insert_query,
                jap_service_id,
                custom_name,
                custom_description,
                custom_price,
                platform,
                "followers",  # default service type
                True,  # is_active
                callback.from_user.id,
                0  # sort_order
            )
            
            if not service_id:
                await callback.message.edit_text(
                    "❌ <b>Failed to publish service</b>\n\n"
                    "⚠️ Error saving to database\n"
                    "💡 Please try again or contact support",
                    parse_mode="HTML"
                )
                await state.clear()
                return
                
        finally:
            # Release the connection back to the pool
            await db_manager.pool.release(db)
        
        # Success message
        text = f"✅ <b>Service Published Successfully!</b>\n\n"
        text += f"📋 <b>Service Details:</b>\n"
        text += f"• JAP Service ID: <b>{jap_service_id}</b>\n"
        text += f"• Custom Name: <b>{custom_name}</b>\n"
        text += f"• Platform: <b>{platform.title()}</b>\n"
        text += f"• Price: <b>{custom_price}</b> coins per 1000 members\n"
        text += f"• Service ID: <b>{service_id}</b>\n\n"
        text += f"💡 <i>This service is now available to users in the {platform.title()} section!</i>"
        
        # Create navigation buttons
        builder = InlineKeyboardBuilder()
        builder.button(text="➕ Add Another Service", callback_data="admin_add_curated_service")
        builder.button(text="📋 List Services", callback_data="admin_list_curated_services")
        builder.button(text="💾 Save as Draft", callback_data="admin_save_draft")
        builder.button(text="🔙 Back to Service Management", callback_data="admin_manage_individual_services")
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
        
        # Clear the state
        await state.clear()
        await callback.answer("✅ Service published successfully!")
        
    except Exception as e:
        logger.error(f"Error publishing service: {e}")
        await callback.answer("❌ Error publishing service")


@router.callback_query(F.data == "admin_save_draft")
async def handle_save_draft(callback: CallbackQuery, state: FSMContext):
    """Save service as draft for later publishing"""
    try:
        # Get all data
        data = await state.get_data()
        jap_service_id = data.get('jap_service_id')
        custom_name = data.get('custom_name')
        platform = data.get('platform', 'general')
        custom_price = data.get('custom_price')
        custom_description = data.get('custom_description')
        
        # Save to database as draft (inactive) using raw SQL
        db = await db_manager.get_connection()
        try:
            # Insert the curated service as draft (inactive)
            insert_query = """
                INSERT INTO admin_curated_services 
                (jap_service_id, custom_name, custom_description, custom_price_per_1000, 
                 platform, service_type, is_active, added_by_admin_id, sort_order)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
            """
            
            service_id = await db.fetchval(
                insert_query,
                jap_service_id,
                custom_name,
                custom_description,
                custom_price,
                platform,
                "followers",  # default service type
                False,  # is_active (draft)
                callback.from_user.id,
                0  # sort_order
            )
            
            if not service_id:
                await callback.message.edit_text(
                    "❌ <b>Failed to save draft</b>\n\n"
                    "⚠️ Error saving to database\n"
                    "💡 Please try again or contact support",
                    parse_mode="HTML"
                )
                await state.clear()
                return
                
        finally:
            # Release the connection back to the pool
            await db_manager.pool.release(db)
        
        # Success message
        text = f"💾 <b>Draft Saved Successfully!</b>\n\n"
        text += f"📋 <b>Draft Details:</b>\n"
        text += f"• JAP Service ID: <b>{jap_service_id}</b>\n"
        text += f"• Custom Name: <b>{custom_name}</b>\n"
        text += f"• Platform: <b>{platform.title()}</b>\n"
        text += f"• Price: <b>{custom_price}</b> coins per 1000 members\n"
        text += f"• Draft ID: <b>{service_id}</b>\n\n"
        text += f"💡 <i>This service is saved as draft and not visible to users yet. You can publish it later from the service list.</i>"
        
        # Create navigation buttons
        builder = InlineKeyboardBuilder()
        builder.button(text="📋 List Services", callback_data="admin_list_curated_services")
        builder.button(text="➕ Add Another Service", callback_data="admin_add_curated_service")
        builder.button(text="🔙 Back to Service Management", callback_data="admin_manage_individual_services")
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
        
        # Clear the state
        await state.clear()

    except Exception as e:
        logger.error(f"Error in save draft: {e}")
        await callback.answer("❌ Error saving draft")


@router.callback_query(F.data == "admin_back_to_jap_id")
async def handle_back_to_jap_id(callback: CallbackQuery, state: FSMContext):
    """Go back to JAP service ID step"""
    try:
        text = "➕ <b>Add New Curated Service</b>\n\n"
        text += "📋 <b>Step 1 of 5: Enter JAP Service ID</b>\n\n"
        text += "Please send the JAP service ID you want to add.\n\n"
        text += "💡 <i>You can find JAP service IDs from the JAP panel or API</i>\n\n"
        text += "📝 <b>Example:</b> 1234"
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Back to Service Management", callback_data="admin_manage_individual_services")
        builder.button(text="❌ Cancel", callback_data="admin_cancel_add_service")
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
        await state.set_state(ServiceManagementStates.waiting_for_jap_service_id)
        await callback.answer("✅ Back to Step 1")
        
    except Exception as e:
        logger.error(f"Error going back to JAP ID: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data == "admin_back_to_custom_name")
async def handle_back_to_custom_name(callback: CallbackQuery, state: FSMContext):
    """Go back to custom name step"""
    try:
        data = await state.get_data()
        jap_service_id = data.get('jap_service_id')
        
        text = f"✅ JAP Service ID: <b>{jap_service_id}</b>\n\n"
        text += "📋 <b>Step 2 of 5: Enter Custom Name</b>\n\n"
        text += "Please send the custom name for this service.\n\n"
        text += "💡 <i>This will be the name users see in the bot</i>\n\n"
        text += "📝 <b>Example:</b> Instagram Followers Premium"
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Back to Step 1", callback_data="admin_back_to_jap_id")
        builder.button(text="❌ Cancel", callback_data="admin_cancel_add_service")
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
        await state.set_state(ServiceManagementStates.waiting_for_custom_name)
        await callback.answer("✅ Back to Step 2")
        
    except Exception as e:
        logger.error(f"Error going back to custom name: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data == "admin_back_to_platform")
async def handle_back_to_platform(callback: CallbackQuery, state: FSMContext):
    """Go back to platform step"""
    try:
        data = await state.get_data()
        jap_service_id = data.get('jap_service_id')
        custom_name = data.get('custom_name')
        
        text = f"✅ JAP Service ID: <b>{jap_service_id}</b>\n"
        text += f"✅ Custom Name: <b>{custom_name}</b>\n\n"
        text += "📋 <b>Step 3 of 5: Select Platform</b>\n\n"
        text += "Please select the platform for this service:\n\n"
        text += "💎 Telegram\n"
        text += "🌟 Instagram\n"
        text += "🚀 TikTok\n"
        text += "🎯 YouTube\n"
        text += "📘 Facebook\n"
        text += "🐦 Twitter\n"
        text += "🛍️ General\n\n"
        text += "💡 <i>Send the platform name (e.g., 'telegram', 'instagram')</i>\n\n"
        text += "📝 <b>Example:</b> instagram"
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Back to Step 2", callback_data="admin_back_to_custom_name")
        builder.button(text="❌ Cancel", callback_data="admin_cancel_add_service")
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
        await state.set_state(ServiceManagementStates.waiting_for_platform)
        await callback.answer("✅ Back to Step 3")
        
    except Exception as e:
        logger.error(f"Error going back to platform: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data == "admin_back_to_price")
async def handle_back_to_price(callback: CallbackQuery, state: FSMContext):
    """Go back to price step"""
    try:
        data = await state.get_data()
        jap_service_id = data.get('jap_service_id')
        custom_name = data.get('custom_name')
        platform = data.get('platform', 'general')
        
        text = f"✅ JAP Service ID: <b>{jap_service_id}</b>\n"
        text += f"✅ Custom Name: <b>{custom_name}</b>\n"
        text += f"✅ Platform: <b>{platform.title()}</b>\n\n"
        text += "📋 <b>Step 4 of 5: Enter Price per 1000 members</b>\n\n"
        text += "Please send the price in coins per 1000 members.\n\n"
        text += "💡 <i>This is the price users will pay per 1000 members</i>\n\n"
        text += "📝 <b>Example:</b> 1500"
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Back to Step 3", callback_data="admin_back_to_platform")
        builder.button(text="❌ Cancel", callback_data="admin_cancel_add_service")
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
        await state.set_state(ServiceManagementStates.waiting_for_custom_price)
        await callback.answer("✅ Back to Step 4")
        
    except Exception as e:
        logger.error(f"Error going back to price: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data == "admin_back_to_description")
async def handle_back_to_description(callback: CallbackQuery, state: FSMContext):
    """Go back to description step"""
    try:
        data = await state.get_data()
        jap_service_id = data.get('jap_service_id')
        custom_name = data.get('custom_name')
        platform = data.get('platform', 'general')
        custom_price = data.get('custom_price')
        
        text = f"✅ JAP Service ID: <b>{jap_service_id}</b>\n"
        text += f"✅ Custom Name: <b>{custom_name}</b>\n"
        text += f"✅ Platform: <b>{platform.title()}</b>\n"
        text += f"✅ Price: <b>{custom_price} coins per 1000 members</b>\n\n"
        text += "📋 <b>Step 5 of 5: Enter Description</b>\n\n"
        text += "Please send a description for this service.\n\n"
        text += "💡 <i>This description will be shown to users</i>\n\n"
        text += "📝 <b>Example:</b> High quality Instagram followers with instant delivery and refill guarantee"
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Back to Step 4", callback_data="admin_back_to_price")
        builder.button(text="❌ Cancel", callback_data="admin_cancel_add_service")
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
        await state.set_state(ServiceManagementStates.waiting_for_custom_description)
        await callback.answer("✅ Back to Step 5")
        
    except Exception as e:
        logger.error(f"Error going back to description: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data == "admin_cancel_add_service")
async def handle_cancel_add_service(callback: CallbackQuery, state: FSMContext):
    """Cancel the add service process"""
    try:
        await state.clear()
        
        text = "❌ <b>Add Service Cancelled</b>\n\n"
        text += "The process has been cancelled. You can start again anytime."
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Back to Service Management", callback_data="admin_manage_individual_services")
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        
        await callback.answer("✅ Add service process cancelled")
        
    except Exception as e:
        logger.error(f"Error cancelling add service: {e}")
        await callback.answer("❌ Error cancelling process")


@router.callback_query(F.data == "admin_list_curated_services")
async def handle_list_curated_services(callback: CallbackQuery):
    """List all curated services"""
    try:
        if not curated_services:
            text = "📋 <b>Curated Services</b>\n\n"
            text += "No curated services found.\n\n"
            text += "💡 <i>Use 'Add Curated Service' to add services for users</i>"
        else:
            text = f"📋 <b>Curated Services ({len(curated_services)})</b>\n\n"
            
            for service_id, service in curated_services.items():
                text += f"🆔 <b>{service_id}</b>\n"
                text += f"• JAP ID: {service['jap_service_id']}\n"
                text += f"• Name: {service['custom_name']}\n"
                text += f"• Price: {service['custom_price']} coins/1K\n"
                text += f"• Status: {'✅ Active' if service['is_active'] else '❌ Inactive'}\n\n"
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Back to Service Management", callback_data="admin_manage_individual_services")
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        
        await callback.answer("✅ Curated services loaded")
        
    except Exception as e:
        logger.error(f"Error listing curated services: {e}")
        await callback.answer("❌ Error loading services list")


@router.callback_query(F.data == "admin_edit_curated_service")
async def handle_edit_curated_service(callback: CallbackQuery):
    """Show edit curated service form"""
    try:
        text = "✏️ <b>Edit Curated Service</b>\n\n"
        text += "📋 <b>Instructions:</b>\n"
        text += "1. Use /list_services to see available services\n"
        text += "2. Use /remove_service <id> to remove a service\n"
        text += "3. Use /add_service to add it back with new settings\n\n"
        text += "💡 <i>For now, you need to remove and re-add services to edit them</i>"
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Back to Service Management", callback_data="admin_manage_individual_services")
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer("✅ Edit service instructions loaded")
        
    except Exception as e:
        logger.error(f"Error in edit curated service: {e}")
        await callback.answer("❌ Error loading edit service form")


@router.callback_query(F.data == "admin_remove_curated_service")
async def handle_remove_curated_service(callback: CallbackQuery):
    """Show remove curated service form"""
    try:
        text = "🗑️ <b>Remove Curated Service</b>\n\n"
        text += "📋 <b>Instructions:</b>\n"
        text += "1. Use /list_services to see available services\n"
        text += "2. Use /remove_service <service_id> to remove a service\n\n"
        text += "📝 <b>Example:</b>\n"
        text += "<code>/remove_service 1</code>\n\n"
        text += "⚠️ <b>Warning:</b> This action cannot be undone!"
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Back to Service Management", callback_data="admin_manage_individual_services")
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer("✅ Remove service instructions loaded")
        
    except Exception as e:
        logger.error(f"Error in remove curated service: {e}")
        await callback.answer("❌ Error loading remove service form")


# Admin Menu Handlers
@router.callback_query(F.data == "admin_users")
async def handle_admin_users(callback: CallbackQuery):
    """Handle admin users management"""
    try:
        text = "👥 <b>User Management</b>\n\n"
        # Get user statistics
        db = await db_manager.get_connection()
        try:
            # Get total users count
            total_users = await db.fetchval("SELECT COUNT(*) FROM users")
            
            # Get users by language
            users_by_lang = await db.fetch("""
                SELECT language, COUNT(*) as count 
                FROM users 
                GROUP BY language 
                ORDER BY count DESC
            """)
            
            # Get recent users (last 7 days)
            recent_users = await db.fetchval("""
                SELECT COUNT(*) FROM users 
                WHERE created_at >= NOW() - INTERVAL '7 days'
            """)
            
            text += f"📊 <b>User Statistics:</b>\n"
            text += f"• Total Users: {total_users}\n"
            text += f"• New Users (7 days): {recent_users}\n\n"
            
            text += f"🌐 <b>Users by Language:</b>\n"
            for row in users_by_lang:
                lang_name = row['language'].title() if row['language'] else 'Unknown'
                text += f"• {lang_name}: {row['count']}\n"
            
            text += f"\n📋 <b>Available Actions:</b>\n"
            text += "• View user details\n"
            text += "• Manage user balances\n"
            text += "• Export user data\n"
            
        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            text += "❌ Error loading user statistics\n"
        finally:
            await db_manager.pool.release(db)
        
        builder = InlineKeyboardBuilder()
        builder.button(text="👥 View All Users", callback_data="admin_view_users")
        builder.button(text="💰 Balance Management", callback_data="admin_balance_mgmt")
        builder.button(text="📊 Export Data", callback_data="admin_export_users")
        builder.button(text="🔙 Back to Admin Menu", callback_data="menu_admin")
        builder.adjust(2, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer("✅ User management loaded")
        
    except Exception as e:
        logger.error(f"Error in admin users: {e}")
        await callback.answer("❌ Error loading user management")


@router.callback_query(F.data == "admin_services")
async def handle_admin_services(callback: CallbackQuery):
    """Handle admin services management"""
    try:
        text = "📊 <b>Service Management</b>\n\n"
        text += "📋 <b>Available Actions:</b>\n"
        text += "• Manage curated services\n"
        text += "• Service availability\n"
        text += "• Pricing management\n"
        text += "• Service analytics\n\n"
        text += "💡 <i>Select an option below</i>"
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🔧 Manage Curated Services", callback_data="admin_manage_individual_services")
        builder.button(text="📈 Service Analytics", callback_data="admin_service_analytics")
        builder.button(text="🔙 Back to Admin Menu", callback_data="menu_admin")
        
        builder.adjust(1, 1, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer("✅ Service management loaded")
        
    except Exception as e:
        logger.error(f"Error in admin services: {e}")
        await callback.answer("❌ Error loading service management")


@router.callback_query(F.data == "admin_payments")
async def handle_admin_payments(callback: CallbackQuery):
    """Handle admin payments management"""
    try:
        text = "💳 <b>Payment Management</b>\n\n"
        # Get payment statistics
        db = await db_manager.get_connection()
        try:
            # Get total transactions count
            total_transactions = await db.fetchval("SELECT COUNT(*) FROM orders")
            
            # Get total revenue
            total_revenue = await db.fetchval("SELECT COALESCE(SUM(amount), 0) FROM orders WHERE status = 'completed'")
            
            # Get transactions by status
            transactions_by_status = await db.fetch("""
                SELECT status, COUNT(*) as count 
                FROM orders 
                GROUP BY status 
                ORDER BY count DESC
            """)
            
            # Get recent transactions (last 7 days)
            recent_transactions = await db.fetchval("""
                SELECT COUNT(*) FROM orders 
                WHERE created_at >= NOW() - INTERVAL '7 days'
            """)
            
            text += f"💰 <b>Payment Statistics:</b>\n"
            text += f"• Total Transactions: {total_transactions}\n"
            text += f"• Total Revenue: {total_revenue:.2f} coins\n"
            text += f"• Recent (7 days): {recent_transactions}\n\n"
            
            text += f"📊 <b>Transactions by Status:</b>\n"
            for row in transactions_by_status:
                status_name = row['status'].title() if row['status'] else 'Unknown'
                text += f"• {status_name}: {row['count']}\n"
            
            text += f"\n📋 <b>Available Actions:</b>\n"
            text += "• View transaction details\n"
            text += "• Process refunds\n"
            text += "• Payment provider settings\n"
            
        except Exception as e:
            logger.error(f"Error getting payment statistics: {e}")
            text += "❌ Error loading payment statistics\n"
        finally:
            await db_manager.pool.release(db)
        
        builder = InlineKeyboardBuilder()
        builder.button(text="💳 View Transactions", callback_data="admin_view_transactions")
        builder.button(text="🔄 Process Refunds", callback_data="admin_refunds")
        builder.button(text="⚙️ Provider Settings", callback_data="admin_payment_settings")
        builder.button(text="🔙 Back to Admin Menu", callback_data="menu_admin")
        builder.adjust(2, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer("✅ Payment management loaded")
        
    except Exception as e:
        logger.error(f"Error in admin payments: {e}")
        await callback.answer("❌ Error loading payment management")


@router.callback_query(F.data == "admin_analytics")
async def handle_admin_analytics(callback: CallbackQuery):
    """Handle admin analytics"""
    try:
        text = "📈 <b>Analytics Dashboard</b>\n\n"
        # Get analytics data
        db = await db_manager.get_connection()
        try:
            # User growth statistics
            total_users = await db.fetchval("SELECT COUNT(*) FROM users")
            users_today = await db.fetchval("""
                SELECT COUNT(*) FROM users 
                WHERE DATE(created_at) = CURRENT_DATE
            """)
            users_this_week = await db.fetchval("""
                SELECT COUNT(*) FROM users 
                WHERE created_at >= NOW() - INTERVAL '7 days'
            """)
            
            # Service usage analytics
            total_services = await db.fetchval("SELECT COUNT(*) FROM admin_curated_services WHERE is_active = true")
            total_orders = await db.fetchval("SELECT COUNT(*) FROM orders")
            
            # Revenue analytics
            total_revenue = await db.fetchval("SELECT COALESCE(SUM(amount), 0) FROM orders WHERE status = 'completed'")
            revenue_today = await db.fetchval("""
                SELECT COALESCE(SUM(amount), 0) FROM orders 
                WHERE status = 'completed' AND DATE(created_at) = CURRENT_DATE
            """)
            
            # Order completion rates
            completed_orders = await db.fetchval("SELECT COUNT(*) FROM orders WHERE status = 'completed'")
            pending_orders = await db.fetchval("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
            failed_orders = await db.fetchval("SELECT COUNT(*) FROM orders WHERE status = 'failed'")
            
            completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
            
            text += f"📈 <b>User Growth:</b>\n"
            text += f"• Total Users: {total_users}\n"
            text += f"• New Today: {users_today}\n"
            text += f"• New This Week: {users_this_week}\n\n"
            
            text += f"🛍️ <b>Service Analytics:</b>\n"
            text += f"• Active Services: {total_services}\n"
            text += f"• Total Orders: {total_orders}\n"
            text += f"• Completion Rate: {completion_rate:.1f}%\n\n"
            
            text += f"💰 <b>Revenue Analytics:</b>\n"
            text += f"• Total Revenue: {total_revenue:.2f} coins\n"
            text += f"• Revenue Today: {revenue_today:.2f} coins\n\n"
            
            text += f"📊 <b>Order Status:</b>\n"
            text += f"• Completed: {completed_orders}\n"
            text += f"• Pending: {pending_orders}\n"
            text += f"• Failed: {failed_orders}\n"
            
        except Exception as e:
            logger.error(f"Error getting analytics data: {e}")
            text += "❌ Error loading analytics data\n"
        finally:
            await db_manager.pool.release(db)
        
        builder = InlineKeyboardBuilder()
        builder.button(text="📊 Detailed Reports", callback_data="admin_detailed_analytics")
        builder.button(text="📈 Growth Charts", callback_data="admin_growth_charts")
        builder.button(text="💰 Revenue Reports", callback_data="admin_revenue_reports")
        builder.button(text="🔙 Back to Admin Menu", callback_data="menu_admin")
        builder.adjust(2, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer("✅ Analytics loaded")
        
    except Exception as e:
        logger.error(f"Error in admin analytics: {e}")
        await callback.answer("❌ Error loading analytics")


# Placeholder handlers for new admin features
@router.callback_query(F.data == "admin_view_users")
async def handle_admin_view_users(callback: CallbackQuery):
    """Handle view all users"""
    await callback.answer("👥 User list feature coming soon!")


@router.callback_query(F.data == "admin_balance_mgmt")
async def handle_admin_balance_mgmt(callback: CallbackQuery):
    """Handle balance management"""
    await callback.answer("💰 Balance management feature coming soon!")


@router.callback_query(F.data == "admin_export_users")
async def handle_admin_export_users(callback: CallbackQuery):
    """Handle export users data"""
    await callback.answer("📊 Export feature coming soon!")


@router.callback_query(F.data == "admin_view_transactions")
async def handle_admin_view_transactions(callback: CallbackQuery):
    """Handle view transactions"""
    await callback.answer("💳 Transaction list feature coming soon!")


@router.callback_query(F.data == "admin_refunds")
async def handle_admin_refunds(callback: CallbackQuery):
    """Handle refunds"""
    await callback.answer("🔄 Refund processing feature coming soon!")


@router.callback_query(F.data == "admin_payment_settings")
async def handle_admin_payment_settings(callback: CallbackQuery):
    """Handle payment settings"""
    await callback.answer("⚙️ Payment settings feature coming soon!")


@router.callback_query(F.data == "admin_detailed_analytics")
async def handle_admin_detailed_analytics(callback: CallbackQuery):
    """Handle detailed analytics"""
    await callback.answer("📊 Detailed analytics feature coming soon!")


@router.callback_query(F.data == "admin_growth_charts")
async def handle_admin_growth_charts(callback: CallbackQuery):
    """Handle growth charts"""
    await callback.answer("📈 Growth charts feature coming soon!")


@router.callback_query(F.data == "admin_revenue_reports")
async def handle_admin_revenue_reports(callback: CallbackQuery):
    """Handle revenue reports"""
    await callback.answer("💰 Revenue reports feature coming soon!")


@router.callback_query(F.data == "admin_service_analytics")
async def handle_admin_service_analytics(callback: CallbackQuery):
    """Handle admin service analytics"""
    try:
        text = "📈 <b>Service Analytics</b>\n\n"
        text += "📊 <b>Service Statistics:</b>\n"
        text += "• Total curated services: 0\n"
        text += "• Active services: 0\n"
        text += "• Total orders: 0\n"
        text += "• Revenue: $0.00\n\n"
        text += "💡 <i>Add services to see analytics</i>"
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Back to Service Management", callback_data="admin_services")
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer("✅ Service analytics loaded")
        
    except Exception as e:
        logger.error(f"Error in service analytics: {e}")
        await callback.answer("❌ Error loading service analytics")
        
        # Add platform sections
        for platform, services in platform_services.items():
            platform_name = platform.title()
            builder.button(
                text=f"🌐 {platform_name} ({len(services)} services)",
                callback_data=f"admin_platform_services_{platform}"
            )
        
        builder.button(text="🔙 Back", callback_data="admin_manage_service_availability")
        
        # Adjust layout based on number of platforms
        if len(platform_services) <= 4:
            builder.adjust(2, 2, 1)
        else:
            builder.adjust(2, 2, 2, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer("✅ Individual service management loaded")
        
    except Exception as e:
        logger.error(f"Error in individual service management: {e}")
        await callback.answer("❌ Error loading services")


# Platform services management
@router.callback_query(F.data.startswith("admin_platform_services_"))
async def handle_platform_services_management(callback: CallbackQuery):
    """Show services for a specific platform"""
    try:
        platform = callback.data.replace("admin_platform_services_", "")
        
        # Get services for this platform
        platform_services = await jap_service.get_services_by_platform(platform)
        
        if not platform_services:
            await callback.answer("❌ No services found for this platform")
            return
        
        platform_name = platform.title()
        text = f"🔧 <b>{platform_name} Service Management</b>\n\n"
        text += f"📊 <b>Services Available:</b> {len(platform_services)}\n\n"
        text += "💡 <i>Select a service to manage its availability</i>"
        
        # Create service selection keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        # Group services by type
        type_services = {}
        for service in platform_services:
            service_type = service.get("service_type", "other")
            if service_type not in type_services:
                type_services[service_type] = []
            type_services[service_type].append(service)
        
        # Add service type sections
        for service_type, services in type_services.items():
            type_name = service_type.title()
            builder.button(
                text=f"🏷️ {type_name} ({len(services)} services)",
                callback_data=f"admin_service_type_{platform}_{service_type}"
            )
        
        builder.button(text="🔙 Back to Platforms", callback_data="admin_manage_individual_services")
        
        # Adjust layout
        if len(type_services) <= 4:
            builder.adjust(2, 2, 1)
        else:
            builder.adjust(2, 2, 2, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer(f"✅ {platform_name} services loaded")
        
    except Exception as e:
        logger.error(f"Error in platform services management: {e}")
        await callback.answer("❌ Error loading platform services")


# Service type management
@router.callback_query(F.data.startswith("admin_service_type_"))
async def handle_service_type_management(callback: CallbackQuery):
    """Show services of a specific type for management"""
    try:
        # Parse callback data: admin_service_type_[platform]_[type]
        parts = callback.data.split("_")
        platform = parts[3]
        service_type = parts[4]
        
        # Get services for this platform and type
        platform_services = await jap_service.get_services_by_platform(platform)
        type_services = [s for s in platform_services if s.get("service_type") == service_type]
        
        if not type_services:
            await callback.answer("❌ No services found for this type")
            return
        
        platform_name = platform.title()
        type_name = service_type.title()
        
        text = f"🔧 <b>{platform_name} {type_name} Services</b>\n\n"
        text += f"📊 <b>Services Available:</b> {len(type_services)}\n\n"
        text += "💡 <i>Select a service to manage its availability</i>"
        
        # Create service selection keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        # Sort services by rate (best price first)
        type_services.sort(key=lambda x: x.get("rate", float('inf')))
        
        # Add individual service buttons (limit to 8 to avoid keyboard overflow)
        for service in type_services[:8]:
            rate = service.get("rate", 0)
            button_text = f"⚡ {service.get('name')} (${rate}/1K)"
            builder.button(
                text=button_text,
                callback_data=f"admin_manage_service_{service.get('id')}"
            )
        
        if len(type_services) > 8:
            builder.button(
                text=f"... and {len(type_services) - 8} more services",
                callback_data="noop"
            )
        
        # Add bulk management options
        builder.button(
            text=f"✅ Enable All {type_name}",
            callback_data=f"admin_enable_all_{platform}_{service_type}"
        )
        builder.button(
            text=f"❌ Disable All {type_name}",
            callback_data=f"admin_disable_all_{platform}_{service_type}"
        )
        
        builder.button(text="🔙 Back to Service Types", callback_data=f"admin_platform_services_{platform}")
        
        # Adjust layout
        builder.adjust(2, 2, 2, 2, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer(f"✅ {type_name} services loaded")
        
    except Exception as e:
        logger.error(f"Error in service type management: {e}")
        await callback.answer("❌ Error loading service type")


# Individual service management
@router.callback_query(F.data.startswith("admin_manage_service_"))
async def handle_manage_individual_service(callback: CallbackQuery):
    """Manage individual service availability"""
    try:
        service_id = int(callback.data.replace("admin_manage_service_", ""))
        
        # Get service details
        all_services = await jap_service.get_services()
        service = None
        for s in all_services:
            if s.get("id") == service_id:
                service = s
                break
        
        if not service:
            await callback.answer("❌ Service not found")
            return
        
        # Show service details and management options
        text = f"🔧 <b>Service Management</b>\n\n"
        text += f"🆔 <b>Service ID:</b> {service.get('id')}\n"
        text += f"📝 <b>Name:</b> {service.get('name')}\n"
        text += f"🏷️ <b>Type:</b> {service.get('type')}\n"
        text += f"📂 <b>Category:</b> {service.get('category')}\n"
        text += f"💰 <b>Rate:</b> ${service.get('rate')}/1000\n"
        text += f"🌐 <b>Platform:</b> {service.get('platform', 'other').title()}\n"
        text += f"🏷️ <b>Service Type:</b> {service.get('service_type', 'other').title()}\n\n"
        text += "💡 <i>Select an action below</i>"
        
        # Create management keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        builder.button(
            text="✅ Enable for All Users",
            callback_data=f"admin_enable_service_{service_id}_global"
        )
        builder.button(
            text="❌ Disable for All Users",
            callback_data=f"admin_disable_service_{service_id}_global"
        )
        builder.button(
            text="👤 Manage Per User",
            callback_data=f"admin_manage_service_user_{service_id}"
        )
        
        builder.button(text="🔙 Back to Services", callback_data=f"admin_service_type_{service.get('platform', 'other')}_{service.get('service_type', 'other')}")
        
        builder.adjust(2, 1, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer(f"✅ Service {service.get('name')} loaded")
        
    except Exception as e:
        logger.error(f"Error in individual service management: {e}")
        await callback.answer("❌ Error loading service")


# Enable/Disable service globally
@router.callback_query(F.data.startswith("admin_enable_service_"))
async def handle_enable_service_global(callback: CallbackQuery):
    """Enable service for all users"""
    try:
        # Parse callback data: admin_enable_service_[id]_global
        service_id = int(callback.data.split("_")[3])
        
        # Enable service globally
        success = await admin_service_manager.set_service_availability(service_id, True)
        
        if success:
            await callback.answer("✅ Service enabled for all users")
            
            # Update the message to show success
            text = callback.message.text + "\n\n✅ <b>Service has been enabled for all users!</b>"
            
            # Create updated keyboard
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            
            builder.button(
                text="❌ Disable for All Users",
                callback_data=f"admin_disable_service_{service_id}_global"
            )
            builder.button(
                text="👤 Manage Per User",
                callback_data=f"admin_manage_service_user_{service_id}"
            )
            builder.button(text="🔙 Back to Services", callback_data="admin_manage_individual_services")
            
            builder.adjust(2, 1)
            
            await callback.message.edit_text(
                text,
                reply_markup=builder.as_markup()
            )
        else:
            await callback.answer("❌ Failed to enable service")
            
    except Exception as e:
        logger.error(f"Error enabling service: {e}")
        await callback.answer("❌ Error enabling service")


# Disable service globally
@router.callback_query(F.data.startswith("admin_disable_service_"))
async def handle_disable_service_global(callback: CallbackQuery):
    """Disable service for all users"""
    try:
        # Parse callback data: admin_disable_service_[id]_global
        service_id = int(callback.data.split("_")[3])
        
        # Disable service globally
        success = await admin_service_manager.set_service_availability(service_id, False)
        
        if success:
            await callback.answer("❌ Service disabled for all users")
            
            # Update the message to show success
            text = callback.message.text + "\n\n❌ <b>Service has been disabled for all users!</b>"
            
            # Create updated keyboard
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            
            builder.button(
                text="✅ Enable for All Users",
                callback_data=f"admin_enable_service_{service_id}_global"
            )
            builder.button(
                text="👤 Manage Per User",
                callback_data=f"admin_manage_service_user_{service_id}"
            )
            builder.button(text="🔙 Back to Services", callback_data="admin_manage_individual_services")
            
            builder.adjust(2, 1)
            
            await callback.message.edit_text(
                text,
                reply_markup=builder.as_markup()
            )
        else:
            await callback.answer("❌ Failed to disable service")
            
    except Exception as e:
        logger.error(f"Error disabling service: {e}")
        await callback.answer("❌ Error disabling service")


# Bulk enable/disable service types
@router.callback_query(F.data.startswith("admin_enable_all_"))
async def handle_enable_all_service_type(callback: CallbackQuery):
    """Enable all services of a specific type"""
    try:
        # Parse callback data: admin_enable_all_[platform]_[type]
        parts = callback.data.split("_")
        platform = parts[3]
        type_name = parts[4]
        
        # Get services for this platform and type
        platform_services = await jap_service.get_services_by_platform(platform)
        type_services = [s for s in platform_services if s.get("service_type") == type_name]
        
        if not type_services:
            await callback.answer("❌ No services found for this type")
            return
        
        # Enable all services of this type
        success_count = 0
        for service in type_services:
            success = await admin_service_manager.set_service_availability(service.get("id"), True)
            if success:
                success_count += 1
        
        await callback.answer(f"✅ {success_count}/{len(type_services)} services enabled")
        
        # Update the message to show success
        text = callback.message.text + f"\n\n✅ <b>{success_count} services have been enabled!</b>"
        
        # Create updated keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        builder.button(
            text=f"❌ Disable All {type_name.title()}",
            callback_data=f"admin_disable_all_{platform}_{type_name}"
        )
        builder.button(text="🔙 Back to Service Types", callback_data=f"admin_platform_services_{platform}")
        
        builder.adjust(2, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error enabling all services: {e}")
        await callback.answer("❌ Error enabling services")


# Bulk disable service types
@router.callback_query(F.data.startswith("admin_disable_all_"))
async def handle_disable_all_service_type(callback: CallbackQuery):
    """Disable all services of a specific type"""
    try:
        # Parse callback data: admin_disable_all_[platform]_[type]
        parts = callback.data.split("_")
        platform = parts[3]
        type_name = parts[4]
        
        # Get services for this platform and type
        platform_services = await jap_service.get_services_by_platform(platform)
        type_services = [s for s in platform_services if s.get("service_type") == type_name]
        
        if not type_services:
            await callback.answer("❌ No services found for this type")
            return
        
        # Disable all services of this type
        success_count = 0
        for service in type_services:
            success = await admin_service_manager.set_service_availability(service.get("id"), False)
            if success:
                success_count += 1
        
        await callback.answer(f"❌ {success_count}/{len(type_services)} services disabled")
        
        # Update the message to show success
        text = callback.message.text + f"\n\n❌ <b>{success_count} services have been disabled!</b>"
        
        # Create updated keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        builder.button(
            text=f"✅ Enable All {type_name.title()}",
            callback_data=f"admin_enable_all_{platform}_{type_name}"
        )
        builder.button(text="🔙 Back to Service Types", callback_data=f"admin_platform_services_{platform}")
        
        builder.adjust(2, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error disabling all services: {e}")
        await callback.answer("❌ Error disabling services")


# Service type management
@router.callback_query(F.data == "admin_manage_service_types")
async def handle_manage_service_types(callback: CallbackQuery):
    """Show service type management options"""
    try:
        text = "🏷️ <b>Service Type Management</b>\n\n"
        text += "📋 <b>Available Service Types:</b>\n"
        text += "• Followers\n"
        text += "• Likes\n"
        text += "• Views\n"
        text += "• Comments\n"
        text += "• Shares\n"
        text += "• Subscribers\n"
        text += "• Members\n\n"
        text += "💡 <i>Select a service type to manage its availability</i>"
        
        # Create service type selection keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        service_types = ["followers", "likes", "views", "comments", "shares", "subscribers", "members"]
        
        for service_type in service_types:
            type_name = service_type.title()
            builder.button(
                text=f"🏷️ {type_name}",
                callback_data=f"admin_manage_type_{service_type}"
            )
        
        builder.button(text="🔙 Back", callback_data="admin_manage_service_availability")
        
        # Adjust layout
        builder.adjust(2, 2, 2, 1, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer("✅ Service type management loaded")
        
    except Exception as e:
        logger.error(f"Error in service type management: {e}")
        await callback.answer("❌ Error loading service types")


# Platform management
@router.callback_query(F.data == "admin_manage_platforms")
async def handle_manage_platforms(callback: CallbackQuery):
    """Show platform management options"""
    try:
        text = "🌐 <b>Platform Management</b>\n\n"
        text += "📋 <b>Available Platforms:</b>\n"
        text += "• Instagram\n"
        text += "• YouTube\n"
        text += "• TikTok\n"
        text += "• Telegram\n"
        text += "• Twitter\n"
        text += "• Facebook\n\n"
        text += "💡 <i>Select a platform to manage its availability</i>"
        
        # Create platform selection keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        platforms = ["instagram", "youtube", "tiktok", "telegram", "twitter", "facebook"]
        
        for platform in platforms:
            platform_name = platform.title()
            builder.button(
                text=f"🌐 {platform_name}",
                callback_data=f"admin_manage_platform_{platform}"
            )
        
        builder.button(text="🔙 Back", callback_data="admin_manage_service_availability")
        
        # Adjust layout
        builder.adjust(2, 2, 2, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer("✅ Platform management loaded")
        
    except Exception as e:
        logger.error(f"Error in platform management: {e}")
        await callback.answer("❌ Error loading platforms")


# User access management
@router.callback_query(F.data == "admin_manage_user_access")
async def handle_manage_user_access(callback: CallbackQuery):
    """Show user access management options"""
    try:
        text = "👥 <b>User Access Management</b>\n\n"
        text += "📋 <b>Available Actions:</b>\n"
        text += "• Set user access levels\n"
        text += "• Manage individual user restrictions\n"
        text += "• View user access statistics\n"
        text += "• Bulk user management\n\n"
        text += "💡 <i>Select an option below</i>"
        
        # Create user access management keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        builder.button(text="👤 Individual User Management", callback_data="admin_individual_user_access")
        builder.button(text="📊 User Access Statistics", callback_data="admin_user_access_stats")
        builder.button(text="🔧 Bulk User Management", callback_data="admin_bulk_user_management")
        builder.button(text="🔙 Back", callback_data="admin_manage_service_availability")
        
        builder.adjust(2, 2, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer("✅ User access management loaded")
        
    except Exception as e:
        logger.error(f"Error in user access management: {e}")
        await callback.answer("❌ Error loading user access options")


# Back to admin service management
@router.callback_query(F.data == "admin_back_to_service_management")
async def handle_back_to_service_management(callback: CallbackQuery):
    """Go back to admin service management menu"""
    await handle_admin_service_management(callback)


# Pricing Management Handlers

@router.callback_query(F.data == "admin_pricing_management")
async def handle_admin_pricing_management(callback: CallbackQuery):
    """Show admin pricing management menu"""
    try:
        # Check if user is admin
        if callback.from_user.id not in settings.admin_ids:
            await callback.answer("❌ Access denied")
            return
        
        # Get pricing statistics
        pricing_stats = await admin_service_manager.get_pricing_statistics()
        
        text = "💰 <b>Admin Pricing Management</b>\n\n"
        text += f"📊 <b>Pricing Statistics:</b>\n"
        
        if "pricing" in pricing_stats:
            pricing = pricing_stats["pricing"]
            text += f"• Total Priced Services: {pricing.get('total_priced_services', 0)}\n"
            text += f"• Markup Services: {pricing.get('markup_services', 0)}\n"
            text += f"• Discount Services: {pricing.get('discount_services', 0)}\n"
            text += f"• Same Price Services: {pricing.get('same_price_services', 0)}\n"
            text += f"• Average Markup: {pricing.get('avg_markup_percentage', 0):.1f}%\n"
        
        text += "\n💡 <i>Select an option to manage pricing</i>"
        
        # Create pricing management keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        builder.button(text="🔧 Manage Individual Service Prices", callback_data="admin_manage_individual_prices")
        builder.button(text="🏷️ Bulk Update Service Type Pricing", callback_data="admin_bulk_service_type_pricing")
        builder.button(text="🌐 Bulk Update Platform Pricing", callback_data="admin_bulk_platform_pricing")
        builder.button(text="📊 Pricing Statistics", callback_data="admin_pricing_statistics")
        builder.button(text="⚙️ Pricing Settings", callback_data="admin_pricing_settings")
        builder.button(text="🔙 Back to Service Management", callback_data="admin_service_management")
        
        builder.adjust(2, 2, 1, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer("✅ Pricing management loaded")
        
    except Exception as e:
        logger.error(f"Error in admin pricing management: {e}")
        await callback.answer("❌ Error loading pricing management")


@router.callback_query(F.data == "admin_manage_individual_prices")
async def handle_manage_individual_prices(callback: CallbackQuery):
    """Show individual service price management"""
    try:
        # Get all services from JAP
        all_services = await jap_service.get_services()
        
        if not all_services:
            await callback.answer("❌ No services available from JAP")
            return
        
        text = "💰 <b>Individual Service Price Management</b>\n\n"
        text += f"📊 <b>Total Services:</b> {len(all_services)}\n\n"
        text += "💡 <i>Select a service to manage its pricing</i>"
        
        # Create service selection keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        # Group services by platform for better organization
        platform_services = {}
        for service in all_services:
            platform = service.get("platform", "other")
            if platform not in platform_services:
                platform_services[platform] = []
            platform_services[platform].append(service)
        
        # Add platform sections
        for platform, services in platform_services.items():
            platform_name = platform.title()
            builder.button(
                text=f"🌐 {platform_name} ({len(services)} services)",
                callback_data=f"admin_price_platform_{platform}"
            )
        
        builder.button(text="🔙 Back", callback_data="admin_pricing_management")
        
        # Adjust layout based on number of platforms
        if len(platform_services) <= 4:
            builder.adjust(2, 2, 1)
        else:
            builder.adjust(2, 2, 2, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer("✅ Individual price management loaded")
        
    except Exception as e:
        logger.error(f"Error in individual price management: {e}")
        await callback.answer("❌ Error loading services")


@router.callback_query(F.data.startswith("admin_price_platform_"))
async def handle_price_platform_services(callback: CallbackQuery):
    """Show services for a specific platform for price management"""
    try:
        platform = callback.data.replace("admin_price_platform_", "")
        
        # Get services for this platform
        platform_services = await jap_service.get_services_by_platform(platform)
        
        if not platform_services:
            await callback.answer("❌ No services found for this platform")
            return
        
        platform_name = platform.title()
        text = f"💰 <b>{platform_name} Price Management</b>\n\n"
        text += f"📊 <b>Services Available:</b> {len(platform_services)}\n\n"
        text += "💡 <i>Select a service to manage its pricing</i>"
        
        # Create service selection keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        # Group services by type
        type_services = {}
        for service in platform_services:
            service_type = service.get("service_type", "other")
            if service_type not in type_services:
                type_services[service_type] = []
            type_services[service_type].append(service)
        
        # Add service type sections
        for service_type, services in type_services.items():
            type_name = service_type.title()
            builder.button(
                text=f"🏷️ {type_name} ({len(services)} services)",
                callback_data=f"admin_price_type_{platform}_{service_type}"
            )
        
        builder.button(text="🔙 Back to Platforms", callback_data="admin_manage_individual_prices")
        
        # Adjust layout
        if len(type_services) <= 4:
            builder.adjust(2, 2, 1)
        else:
            builder.adjust(2, 2, 2, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer(f"✅ {platform_name} price management loaded")
        
    except Exception as e:
        logger.error(f"Error in platform price management: {e}")
        await callback.answer("❌ Error loading platform services")


@router.callback_query(F.data.startswith("admin_price_type_"))
async def handle_price_service_type(callback: CallbackQuery):
    """Show services of a specific type for price management"""
    try:
        # Parse callback data: admin_price_type_[platform]_[type]
        parts = callback.data.split("_")
        platform = parts[3]
        service_type = parts[4]
        
        # Get services for this platform and type
        platform_services = await jap_service.get_services_by_platform(platform)
        type_services = [s for s in platform_services if s.get("service_type") == service_type]
        
        if not type_services:
            await callback.answer("❌ No services found for this type")
            return
        
        platform_name = platform.title()
        type_name = service_type.title()
        
        text = f"💰 <b>{platform_name} {type_name} Price Management</b>\n\n"
        text += f"📊 <b>Services Available:</b> {len(type_services)}\n\n"
        text += "💡 <i>Select a service to manage its pricing</i>"
        
        # Create service selection keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        # Sort services by rate (best price first)
        type_services.sort(key=lambda x: x.get("rate", float('inf')))
        
        # Add individual service buttons (limit to 8 to avoid keyboard overflow)
        for service in type_services[:8]:
            rate = service.get("rate", 0)
            button_text = f"⚡ {service.get('name')} (${rate}/1K)"
            builder.button(
                text=button_text,
                callback_data=f"admin_manage_price_{service.get('id')}"
            )
        
        if len(type_services) > 8:
            builder.button(
                text=f"... and {len(type_services) - 8} more services",
                callback_data="noop"
            )
        
        # Add bulk pricing options
        builder.button(
            text=f"💰 Set {type_name} Markup %",
            callback_data=f"admin_set_type_markup_{platform}_{service_type}"
        )
        builder.button(
            text=f"🔄 Reset {type_name} to Default",
            callback_data=f"admin_reset_type_pricing_{platform}_{service_type}"
        )
        
        builder.button(text="🔙 Back to Service Types", callback_data=f"admin_price_platform_{platform}")
        
        # Adjust layout
        builder.adjust(2, 2, 2, 2, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer(f"✅ {type_name} price management loaded")
        
    except Exception as e:
        logger.error(f"Error in service type price management: {e}")
        await callback.answer("❌ Error loading service type")


@router.callback_query(F.data.startswith("admin_manage_price_"))
async def handle_manage_individual_price(callback: CallbackQuery):
    """Manage individual service pricing"""
    try:
        service_id_str = callback.data.replace("admin_manage_price_", "")
        if service_id_str == "None" or not service_id_str:
            await callback.answer("❌ Invalid service ID")
            return
        service_id = int(service_id_str)
        
        # Get service details and pricing
        all_services = await jap_service.get_services()
        service = None
        for s in all_services:
            if s.get("id") == service_id:
                service = s
                break
        
        if not service:
            await callback.answer("❌ Service not found")
            return
        
        # Get pricing information
        pricing_info = await admin_service_manager.get_service_pricing(service_id, for_admin=True)
        
        if not pricing_info:
            await callback.answer("❌ Pricing information not found")
            return
        
        # Show service details and pricing
        text = f"💰 <b>Service Price Management</b>\n\n"
        text += f"🆔 <b>Service ID:</b> {service.get('id')}\n"
        text += f"📝 <b>Name:</b> {service.get('name')}\n"
        text += f"🌐 <b>Platform:</b> {service.get('platform', 'other').title()}\n"
        text += f"🏷️ <b>Type:</b> {service.get('service_type', 'other').title()}\n\n"
        
        text += f"💵 <b>Pricing Information:</b>\n"
        text += f"• JAP Price: ${pricing_info.get('jap_price_usd', 0):.4f}/1000\n"
        text += f"• Custom Price: ${pricing_info.get('custom_price_usd', 0):.4f}/1000\n"
        text += f"• Price in Coins: {pricing_info.get('custom_price_coins', 0)}/1000\n"
        text += f"• Markup: {pricing_info.get('markup_percentage', 0):.1f}%\n"
        text += f"• Price Difference: ${pricing_info.get('price_difference_usd', 0):.4f}\n"
        text += f"• Difference %: {pricing_info.get('price_difference_percentage', 0):.1f}%\n\n"
        
        if pricing_info.get("is_default_pricing"):
            text += "⚠️ <i>Using default pricing (no custom price set)</i>\n\n"
        
        text += "💡 <i>Select an action below</i>"
        
        # Create pricing management keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        builder.button(
            text="💰 Set Custom Price",
            callback_data=f"admin_set_custom_price_{service_id}"
        )
        builder.button(
            text="📊 Set Markup %",
            callback_data=f"admin_set_markup_{service_id}"
        )
        builder.button(
            text="🔄 Reset to Default",
            callback_data=f"admin_reset_pricing_{service_id}"
        )
        
        builder.button(text="🔙 Back to Services", callback_data=f"admin_price_type_{service.get('platform', 'other')}_{service.get('service_type', 'other')}")
        
        builder.adjust(2, 1, 1)
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        await callback.answer(f"✅ {service.get('name')} pricing loaded")
        
    except Exception as e:
        logger.error(f"Error in individual price management: {e}")
        await callback.answer("❌ Error loading service pricing")


@router.callback_query(F.data.startswith("admin_set_custom_price_"))
async def handle_set_custom_price(callback: CallbackQuery, state: FSMContext):
    """Set custom price for a service"""
    try:
        service_id = int(callback.data.replace("admin_set_custom_price_", ""))
        
        # Store service ID in state
        await state.update_data(service_id=service_id, action="set_custom_price")
        
        text = f"💰 <b>Set Custom Price</b>\n\n"
        text += f"🆔 <b>Service ID:</b> {service_id}\n\n"
        text += "💡 <i>Please enter the new price per 1000 in USD (e.g., 0.50)</i>"
        
        # Create input keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        builder.button(text="❌ Cancel", callback_data=f"admin_manage_price_{service_id}")
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        # Set state to wait for price input
        await state.set_state(ServiceManagementStates.waiting_for_custom_price)
        
        await callback.answer("✅ Enter the new price")
        
    except Exception as e:
        logger.error(f"Error setting custom price: {e}")
        await callback.answer("❌ Error setting custom price")


@router.message(ServiceManagementStates.waiting_for_custom_price)
async def handle_custom_price_input(message: Message, state: FSMContext):
    """Handle custom price input"""
    try:
        # Get service ID from state
        data = await state.get_data()
        service_id = data.get("service_id")
        
        if not service_id:
            await message.answer("❌ Service ID not found. Please try again.")
            await state.clear()
            return
        
        # Parse price input
        try:
            custom_price = float(message.text.strip())
            if custom_price <= 0:
                await message.answer("❌ Price must be greater than 0. Please try again.")
                return
        except ValueError:
            await message.answer("❌ Invalid price format. Please enter a valid number (e.g., 0.50)")
            return
        
        # Set the custom price
        success = await admin_service_manager.set_service_price(service_id, custom_price)
        
        if success:
            await message.answer(f"✅ Price updated successfully!\n💰 New price: ${custom_price}/1000")
            
            # Go back to service pricing management
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.button(text="🔙 Back to Service", callback_data=f"admin_manage_price_{service_id}")
            
            await message.answer(
                "💡 <i>Price has been updated. Users will now see the new price.</i>",
                reply_markup=builder.as_markup()
            )
        else:
            await message.answer("❌ Failed to update price. Please try again.")
        
        # Clear state
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error handling custom price input: {e}")
        await message.answer("❌ Error updating price. Please try again.")
        await state.clear()


@router.callback_query(F.data.startswith("admin_set_markup_"))
async def handle_set_markup(callback: CallbackQuery, state: FSMContext):
    """Set markup percentage for a service"""
    try:
        service_id = int(callback.data.replace("admin_set_markup_", ""))
        
        # Store service ID in state
        await state.update_data(service_id=service_id, action="set_markup")
        
        text = f"📊 <b>Set Markup Percentage</b>\n\n"
        text += f"🆔 <b>Service ID:</b> {service_id}\n\n"
        text += "💡 <i>Please enter the markup percentage (e.g., 20 for 20%)</i>"
        
        # Create input keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        builder.button(text="❌ Cancel", callback_data=f"admin_manage_price_{service_id}")
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
        # Set state to wait for markup input
        await state.set_state(ServiceManagementStates.waiting_for_markup)
        
        await callback.answer("✅ Enter the markup percentage")
        
    except Exception as e:
        logger.error(f"Error setting markup: {e}")
        await callback.answer("❌ Error setting markup")


@router.message(ServiceManagementStates.waiting_for_markup)
async def handle_markup_input(message: Message, state: FSMContext):
    """Handle markup percentage input"""
    try:
        # Get service ID from state
        data = await state.get_data()
        service_id = data.get("service_id")
        
        if not service_id:
            await message.answer("❌ Service ID not found. Please try again.")
            await state.clear()
            return
        
        # Parse markup input
        try:
            markup = float(message.text.strip())
            if markup < -100:
                await message.answer("❌ Markup cannot be less than -100%. Please try again.")
                return
        except ValueError:
            await message.answer("❌ Invalid markup format. Please enter a valid number (e.g., 20)")
            return
        
        # Get JAP price and calculate new custom price
        all_services = await jap_service.get_services()
        jap_service_data = None
        for service in all_services:
            if service.get("id") == service_id:
                jap_service_data = service
                break
        
        if not jap_service_data:
            await message.answer("❌ Service not found. Please try again.")
            await state.clear()
            return
        
        jap_price = jap_service_data.get("rate", 0)
        if jap_price <= 0:
            await message.answer("❌ Invalid JAP price. Please try again.")
            await state.clear()
            return
        
        # Calculate new custom price
        custom_price = jap_price * (1 + markup / 100)
        
        # Set the custom price with markup
        success = await admin_service_manager.set_service_price(service_id, custom_price, markup)
        
        if success:
            await message.answer(
                f"✅ Markup updated successfully!\n"
                f"💰 JAP Price: ${jap_price:.4f}/1000\n"
                f"📊 Markup: {markup:.1f}%\n"
                f"💵 New Price: ${custom_price:.4f}/1000"
            )
            
            # Go back to service pricing management
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.button(text="🔙 Back to Service", callback_data=f"admin_manage_price_{service_id}")
            
            await message.answer(
                "💡 <i>Markup has been updated. Users will now see the new price.</i>",
                reply_markup=builder.as_markup()
            )
        else:
            await message.answer("❌ Failed to update markup. Please try again.")
        
        # Clear state
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error handling markup input: {e}")
        await message.answer("❌ Error updating markup. Please try again.")
        await state.clear()


@router.callback_query(F.data.startswith("admin_reset_pricing_"))
async def handle_reset_pricing(callback: CallbackQuery):
    """Reset service pricing to default"""
    try:
        service_id = int(callback.data.replace("admin_reset_pricing_", ""))
        
        # Get JAP service data
        all_services = await jap_service.get_services()
        jap_service_data = None
        for service in all_services:
            if service.get("id") == service_id:
                jap_service_data = service
                break
        
        if not jap_service_data:
            await callback.answer("❌ Service not found")
            return
        
        # Get default markup
        default_markup = float(await admin_service_manager.get_setting("default_markup_percentage", "20.0"))
        jap_price = jap_service_data.get("rate", 0)
        
        if jap_price <= 0:
            await callback.answer("❌ Invalid JAP price")
            return
        
        # Calculate default custom price
        default_custom_price = jap_price * (1 + default_markup / 100)
        
        # Set the default pricing
        success = await admin_service_manager.set_service_price(service_id, default_custom_price, default_markup)
        
        if success:
            await callback.answer(f"✅ Pricing reset to default ({default_markup}% markup)")
            
            # Update the message to show reset
            text = callback.message.text + f"\n\n🔄 <b>Pricing has been reset to default!</b>\n💰 Default Price: ${default_custom_price:.4f}/1000\n📊 Markup: {default_markup}%"
            
            # Create updated keyboard
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            
            builder.button(
                text="💰 Set Custom Price",
                callback_data=f"admin_set_custom_price_{service_id}"
            )
            builder.button(
                text="📊 Set Markup %",
                callback_data=f"admin_set_markup_{service_id}"
            )
            builder.button(
                text="🔄 Reset to Default",
                callback_data=f"admin_reset_pricing_{service_id}"
            )
            
            builder.button(text="🔙 Back to Services", callback_data=f"admin_price_type_{jap_service_data.get('platform', 'other')}_{jap_service_data.get('service_type', 'other')}")
            
            builder.adjust(2, 1, 1)
            
            await callback.message.edit_text(
                text,
                reply_markup=builder.as_markup()
            )
        else:
            await callback.answer("❌ Failed to reset pricing")
            
    except Exception as e:
        logger.error(f"Error resetting pricing: {e}")
        await callback.answer("❌ Error resetting pricing")


# Add missing states
@router.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery):
    """Handle no-op callback (for buttons that don't need action)"""
    await callback.answer("ℹ️ This option is not yet implemented")


# Add new service handler
@router.callback_query(F.data == "admin_add_service")
async def handle_add_service(callback: CallbackQuery, state: FSMContext):
    """Handle add new service"""
    try:
        # Check if user is admin
        if callback.from_user.id not in settings.admin_ids:
            await callback.answer("❌ Access denied")
            return
        
        await state.set_state(ServiceManagementStates.waiting_for_service_code)
        
        text = "➕ <b>Add New Service</b>\n\n"
        text += "📋 <b>Instructions:</b>\n"
        text += "1. Find the service ID from JAP panel\n"
        text += "2. Send the service ID number\n"
        text += "3. Service will be added for admin approval\n"
        text += "4. After approval and pricing, it becomes available to users\n\n"
        text += "💡 <i>Send the service ID number now...</i>"
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Back to Service Management", callback_data="admin_service_management")
        
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error in add service: {e}")
        await callback.answer("❌ Error")

# Handle service code input
@router.message(ServiceManagementStates.waiting_for_service_code)
async def handle_service_code_input(message: Message, state: FSMContext):
    """Handle service code input"""
    try:
        # Check if user is admin
        if message.from_user.id not in settings.admin_ids:
            await message.answer("❌ Access denied")
            return
        
        try:
            service_id = int(message.text.strip())
        except ValueError:
            await message.answer("❌ Please enter a valid service ID number")
            return
        
        # Add service to cache
        result = await admin_service_manager.add_service_by_code(service_id, message.from_user.id)
        
        if result["success"]:
            service = result["service"]
            text = f"✅ <b>Service Added Successfully!</b>\n\n"
            text += f"🆔 <b>Service ID:</b> {service['id']}\n"
            text += f"📝 <b>Name:</b> {service['name']}\n"
            text += f"🌐 <b>Platform:</b> {service['platform'].title()}\n"
            text += f"🏷️ <b>Type:</b> {service['service_type'].title()}\n"
            text += f"💰 <b>JAP Rate:</b> ${service['rate']:.4f}\n\n"
            text += f"⏳ <b>Status:</b> Pending Admin Approval\n"
            text += f"💡 <i>Use 'Pending Approvals' to approve and set pricing</i>"
        else:
            text = f"❌ <b>Error Adding Service</b>\n\n"
            text += f"🔍 <b>Error:</b> {result['error']}\n\n"
            text += f"💡 <i>Make sure the service ID exists in JAP</i>"
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Back to Service Management", callback_data="admin_service_management")
        builder.button(text="⏳ View Pending Approvals", callback_data="admin_pending_services")
        
        await message.answer(text, reply_markup=builder.as_markup())
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error in service code input: {e}")
        await message.answer("❌ Error processing service code")

# Pending services handler
@router.callback_query(F.data == "admin_pending_services")
async def handle_pending_services(callback: CallbackQuery):
    """Handle pending services approval"""
    try:
        # Check if user is admin
        if callback.from_user.id not in settings.admin_ids:
            await callback.answer("❌ Access denied")
            return
        
        pending_services = await admin_service_manager.get_pending_services()
        
        if not pending_services:
            text = "⏳ <b>Pending Service Approvals</b>\n\n"
            text += "✅ <b>No services pending approval</b>\n\n"
            text += "💡 <i>All services are approved and ready</i>"
            
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.button(text="🔙 Back to Service Management", callback_data="admin_service_management")
            
            await callback.message.edit_text(text, reply_markup=builder.as_markup())
            return
        
        text = f"⏳ <b>Pending Service Approvals</b>\n\n"
        text += f"📊 <b>Total Pending:</b> {len(pending_services)}\n\n"
        
        # Show first few services
        for i, service in enumerate(pending_services[:5]):
            text += f"🆔 <b>ID:</b> {service['service_id']}\n"
            text += f"📝 <b>Name:</b> {service['name'][:50]}...\n"
            text += f"🌐 <b>Platform:</b> {service['platform'].title()}\n"
            text += f"💰 <b>Rate:</b> ${service['rate']:.4f}\n"
            text += f"📅 <b>Added:</b> {service['created_at'].strftime('%Y-%m-%d')}\n\n"
        
        if len(pending_services) > 5:
            text += f"... and {len(pending_services) - 5} more services\n\n"
        
        text += "💡 <i>Click on a service to approve it</i>"
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        # Add buttons for first few services
        for service in pending_services[:5]:
            builder.button(
                text=f"✅ Approve {service['service_id']}",
                callback_data=f"approve_service_{service['service_id']}"
            )
        
        builder.button(text="🔙 Back to Service Management", callback_data="admin_service_management")
        builder.adjust(1, 1, 1, 1, 1, 1)
        
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
        
    except Exception as e:
        logger.error(f"Error in pending services: {e}")
        await callback.answer("❌ Error")

# Approve service handler
@router.callback_query(F.data.startswith("approve_service_"))
async def handle_approve_service(callback: CallbackQuery):
    """Handle service approval"""
    try:
        # Check if user is admin
        if callback.from_user.id not in settings.admin_ids:
            await callback.answer("❌ Access denied")
            return
        
        service_id = int(callback.data.split("_")[2])
        
        # Approve the service
        success = await admin_service_manager.approve_service(service_id, callback.from_user.id)
        
        if success:
            text = f"✅ <b>Service Approved!</b>\n\n"
            text += f"🆔 <b>Service ID:</b> {service_id}\n"
            text += f"👤 <b>Approved by:</b> {callback.from_user.first_name}\n"
            text += f"📅 <b>Approved at:</b> {callback.message.date.strftime('%Y-%m-%d %H:%M')}\n\n"
            text += f"💰 <b>Next Step:</b> Set pricing in Pricing Management\n"
            text += f"💡 <i>Service is now available for pricing configuration</i>"
        else:
            text = f"❌ <b>Error Approving Service</b>\n\n"
            text += f"🆔 <b>Service ID:</b> {service_id}\n"
            text += f"💡 <i>Please try again or contact support</i>"
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="⏳ View More Pending", callback_data="admin_pending_services")
        builder.button(text="💰 Set Pricing", callback_data="admin_pricing_management")
        builder.button(text="🔙 Back to Service Management", callback_data="admin_service_management")
        
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
        await callback.answer("✅ Service approved!" if success else "❌ Approval failed")
        
    except Exception as e:
        logger.error(f"Error in approve service: {e}")
        await callback.answer("❌ Error")


def setup(dispatcher):
    """Setup admin handlers"""
    dispatcher.include_router(router)

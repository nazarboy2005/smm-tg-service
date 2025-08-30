"""
Admin handlers for the Telegram bot
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from sqlalchemy import select
from bot.database.db import get_db
from bot.services.user_service import UserService
from bot.services.admin_service import AdminService
from bot.services.service_service import ServiceService
from bot.database.models import ServiceCategory, Service
from bot.utils.i18n import get_text, Language
from bot.utils.keyboards import get_admin_menu_keyboard, get_back_keyboard
from bot.middleware.security_middleware import AdminOnlyMiddleware

# Create router with admin middleware
router = Router()
router.message.middleware(AdminOnlyMiddleware())
router.callback_query.middleware(AdminOnlyMiddleware())


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Handle /admin command"""
    try:
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, message.from_user.id)
            if user:
                language = Language(user.language.value)
                
                # Get dashboard stats
                stats = await AdminService.get_dashboard_stats(db)
                
                text = f"👑 {get_text('admin_menu', language)}\n\n"
                text += f"📊 **Dashboard Stats:**\n"
                text += f"👥 Users: {stats.get('users', {}).get('total', 0)}\n"
                text += f"💰 Total Deposits: ${stats.get('financial', {}).get('total_deposits_usd', 0):.2f}\n"
                text += f"📋 Total Orders: {stats.get('orders', {}).get('total', 0)}\n"
                text += f"✅ Completed: {stats.get('orders', {}).get('completed', 0)}\n"
                
                await message.answer(
                    text,
                    reply_markup=get_admin_menu_keyboard(language)
                )
            break
    except Exception as e:
        logger.error(f"Error in admin command: {e}")
        await message.answer("❌ Error loading admin panel")


@router.callback_query(F.data == "menu_admin")
async def handle_admin_menu(callback: CallbackQuery):
    """Handle admin menu"""
    try:
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                language = Language(user.language.value)
                
                stats = await AdminService.get_dashboard_stats(db)
                
                text = f"👑 {get_text('admin_menu', language)}\n\n"
                text += f"📊 **Quick Stats:**\n"
                text += f"👥 Total Users: {stats.get('users', {}).get('total', 0)}\n"
                text += f"🆕 New Today: {stats.get('users', {}).get('new_today', 0)}\n"
                text += f"💰 Total Revenue: ${stats.get('financial', {}).get('total_revenue_usd', 0):.2f}\n"
                text += f"📋 Total Orders: {stats.get('orders', {}).get('total', 0)}\n"
                
                await callback.message.edit_text(
                    text,
                    reply_markup=get_admin_menu_keyboard(language)
                )
            break
    except Exception as e:
        logger.error(f"Error in admin menu: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data == "admin_users")
async def handle_admin_users(callback: CallbackQuery):
    """Handle user management"""
    try:
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                language = Language(user.language.value)
                
                # Get recent users
                users, total_count = await AdminService.get_users_list(db, page=1, per_page=10)
                
                text = f"👥 {get_text('user_management', language)}\n\n"
                text += f"📊 Total Users: {total_count}\n\n"
                
                if users:
                    text += "**Recent Users:**\n"
                    for u in users[:5]:
                        balance = u.balance.coins if u.balance else 0
                        text += f"• {u.first_name or 'N/A'} (@{u.username or 'N/A'}) - {balance} coins\n"
                else:
                    text += "No users found."
                
                await callback.message.edit_text(
                    text,
                    reply_markup=get_back_keyboard(language, "menu_admin")
                )
            break
    except Exception as e:
        logger.error(f"Error in admin users: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data == "admin_services")
async def handle_admin_services(callback: CallbackQuery):
    """Handle service management"""
    try:
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                language = Language(user.language.value)
                
                # Get service stats
                stats = await ServiceService.get_services_stats(db)
                
                # Create keyboard for service management
                builder = InlineKeyboardBuilder()
                
                # Add buttons for service management
                builder.button(
                    text="📋 View Categories",
                    callback_data="admin_view_categories"
                )
                builder.button(
                    text="🔍 Search Services",
                    callback_data="admin_search_services"
                )
                builder.button(
                    text="🔄 Sync Services",
                    callback_data="admin_sync_services"
                )
                builder.button(
                    text="⬅️ Back",
                    callback_data="menu_admin"
                )
                
                builder.adjust(1)
                
                text = f"📊 {get_text('service_management', language)}\n\n"
                text += f"🔧 Total Services: {stats.get('total_services', 0)}\n"
                text += f"✅ Active: {stats.get('active_services', 0)}\n"
                text += f"❌ Inactive: {stats.get('inactive_services', 0)}\n"
                text += f"📂 Categories: {stats.get('total_categories', 0)}\n\n"
                text += "Select an option to manage services:"
                
                await callback.message.edit_text(
                    text,
                    reply_markup=builder.as_markup()
                )
            break
    except Exception as e:
        logger.error(f"Error in admin services: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data == "admin_analytics")
async def handle_admin_analytics(callback: CallbackQuery):
    """Handle analytics dashboard"""
    try:
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                language = Language(user.language.value)
                
                # Get analytics data
                analytics = await AdminService.get_analytics_data(db, days=7)
                
                text = f"📈 {get_text('analytics', language)} ({get_text('last_7_days', language)})\n\n"
                
                # Registrations
                registrations = analytics.get('registrations', [])
                total_reg = sum(r['count'] for r in registrations)
                text += f"👥 New Users: {total_reg}\n"
                
                # Deposits
                deposits = analytics.get('deposits', [])
                total_dep = sum(d['amount'] for d in deposits)
                text += f"💰 Deposits: ${total_dep:.2f}\n"
                
                # Orders
                orders = analytics.get('orders', [])
                total_ord = sum(o['count'] for o in orders)
                total_rev = sum(o['revenue_usd'] for o in orders)
                text += f"📋 Orders: {total_ord}\n"
                text += f"💵 Revenue: ${total_rev:.2f}\n"
                
                await callback.message.edit_text(
                    text,
                    reply_markup=get_back_keyboard(language, "menu_admin")
                )
            break
    except Exception as e:
        logger.error(f"Error in admin analytics: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data == "admin_view_categories")
async def handle_admin_view_categories(callback: CallbackQuery):
    """Handle viewing service categories"""
    try:
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                language = Language(user.language.value)
                
                # Get all categories (including inactive)
                result = await db.execute(
                    select(ServiceCategory).order_by(ServiceCategory.sort_order, ServiceCategory.name)
                )
                categories = result.scalars().all()
                
                builder = InlineKeyboardBuilder()
                
                # Add buttons for each category
                for category in categories:
                    status = "✅" if category.is_active else "❌"
                    builder.button(
                        text=f"{status} {category.name}",
                        callback_data=f"admin_category_{category.id}"
                    )
                
                builder.button(
                    text="⬅️ Back",
                    callback_data="admin_services"
                )
                
                builder.adjust(1)
                
                text = f"📂 Service Categories\n\n"
                text += "Select a category to view and manage its services:"
                
                await callback.message.edit_text(
                    text,
                    reply_markup=builder.as_markup()
                )
            break
    except Exception as e:
        logger.error(f"Error in admin view categories: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data.startswith("admin_category_"))
async def handle_admin_category_services(callback: CallbackQuery):
    """Handle viewing services in a category"""
    try:
        category_id = int(callback.data.replace("admin_category_", ""))
        
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                language = Language(user.language.value)
                
                # Get category
                result = await db.execute(
                    select(ServiceCategory).where(ServiceCategory.id == category_id)
                )
                category = result.scalar_one_or_none()
                
                if not category:
                    await callback.answer("❌ Category not found")
                    return
                
                # Get all services in category (including inactive)
                result = await db.execute(
                    select(Service)
                    .where(Service.category_id == category_id)
                    .order_by(Service.sort_order, Service.name)
                )
                services = result.scalars().all()
                
                builder = InlineKeyboardBuilder()
                
                # Add buttons for each service
                for service in services:
                    status = "✅" if service.is_active else "❌"
                    builder.button(
                        text=f"{status} {service.name[:30]}",
                        callback_data=f"admin_service_{service.id}"
                    )
                
                builder.button(
                    text="⬅️ Back to Categories",
                    callback_data="admin_view_categories"
                )
                
                builder.adjust(1)
                
                text = f"📊 Services in {category.name}\n\n"
                if services:
                    text += "Select a service to manage:"
                else:
                    text += "No services found in this category."
                
                await callback.message.edit_text(
                    text,
                    reply_markup=builder.as_markup()
                )
            break
    except Exception as e:
        logger.error(f"Error in admin category services: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data.startswith("admin_service_"))
async def handle_admin_service_details(callback: CallbackQuery):
    """Handle viewing service details"""
    try:
        service_id = int(callback.data.replace("admin_service_", ""))
        
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                language = Language(user.language.value)
                
                # Get service
                service = await ServiceService.get_service_by_id(db, service_id)
                
                if not service:
                    await callback.answer("❌ Service not found")
                    return
                
                # Create keyboard for service management
                builder = InlineKeyboardBuilder()
                
                # Toggle active status
                if service.is_active:
                    builder.button(
                        text="❌ Deactivate Service",
                        callback_data=f"admin_toggle_service_{service_id}_0"
                    )
                else:
                    builder.button(
                        text="✅ Activate Service",
                        callback_data=f"admin_toggle_service_{service_id}_1"
                    )
                
                # Edit price
                builder.button(
                    text="💰 Edit Price",
                    callback_data=f"admin_edit_price_{service_id}"
                )
                
                # Back button
                builder.button(
                    text="⬅️ Back to Services",
                    callback_data=f"admin_category_{service.category_id}"
                )
                
                builder.adjust(1)
                
                # Format service details
                text = f"📊 Service Details\n\n"
                text += f"📝 Name: {service.name}\n"
                text += f"📂 Category: {service.category.name}\n"
                text += f"💰 Price per 1K: {service.price_per_1000} coins\n"
                text += f"📊 Min Quantity: {service.min_quantity}\n"
                text += f"📊 Max Quantity: {service.max_quantity}\n"
                text += f"📝 Description: {service.description or 'N/A'}\n"
                text += f"🔧 Status: {'✅ Active' if service.is_active else '❌ Inactive'}\n"
                
                await callback.message.edit_text(
                    text,
                    reply_markup=builder.as_markup()
                )
            break
    except Exception as e:
        logger.error(f"Error in admin service details: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data.startswith("admin_toggle_service_"))
async def handle_admin_toggle_service(callback: CallbackQuery):
    """Handle toggling service active status"""
    try:
        # Parse service_id and new status
        parts = callback.data.split("_")
        service_id = int(parts[3])
        is_active = parts[4] == "1"
        
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                # Update service status
                success = await ServiceService.update_service_status(db, service_id, is_active)
                
                if success:
                    await callback.answer(f"Service {'activated' if is_active else 'deactivated'} successfully!")
                    # Reload service details
                    await handle_admin_service_details(callback)
                else:
                    await callback.answer("❌ Failed to update service status")
            break
    except Exception as e:
        logger.error(f"Error toggling service status: {e}")
        await callback.answer("❌ Error")


@router.callback_query(F.data == "admin_sync_services")
async def handle_admin_sync_services(callback: CallbackQuery):
    """Handle syncing services from JAP API"""
    try:
        await callback.answer("🔄 Syncing services...")
        
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, callback.from_user.id)
            if user:
                language = Language(user.language.value)
                
                success = await ServiceService.sync_services_from_jap(db)
                
                text = f"🔄 Service Sync\n\n"
                if success:
                    text += "✅ Services synced successfully from JAP API!"
                else:
                    text += "❌ Failed to sync services. Check logs for details."
                
                await callback.message.edit_text(
                    text,
                    reply_markup=get_back_keyboard(language, "admin_services")
                )
            break
    except Exception as e:
        logger.error(f"Error syncing services: {e}")
        await callback.answer("❌ Error syncing services")


@router.message(Command("sync_services"))
async def cmd_sync_services(message: Message):
    """Sync services from JAP API"""
    try:
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, message.from_user.id)
            if user and user.is_admin:
                await message.answer("🔄 Syncing services from JAP API...")
                
                success = await ServiceService.sync_services_from_jap(db)
                
                if success:
                    await message.answer("✅ Services synced successfully!")
                else:
                    await message.answer("❌ Failed to sync services. Check logs for details.")
            break
    except Exception as e:
        logger.error(f"Error in sync services command: {e}")
        await message.answer("❌ Error syncing services")


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Get quick stats"""
    try:
        async for db in get_db():
            user = await UserService.get_user_by_telegram_id(db, message.from_user.id)
            if user and user.is_admin:
                stats = await AdminService.get_dashboard_stats(db)
                
                text = "📊 **Bot Statistics**\n\n"
                
                # Users
                users = stats.get('users', {})
                text += f"👥 **Users:**\n"
                text += f"• Total: {users.get('total', 0)}\n"
                text += f"• Active (7d): {users.get('active_week', 0)}\n"
                text += f"• New Today: {users.get('new_today', 0)}\n\n"
                
                # Financial
                financial = stats.get('financial', {})
                text += f"💰 **Financial:**\n"
                text += f"• Deposits: ${financial.get('total_deposits_usd', 0):.2f}\n"
                text += f"• Revenue: ${financial.get('total_revenue_usd', 0):.2f}\n"
                text += f"• Balance: {financial.get('total_balance_coins', 0):.0f} coins\n\n"
                
                # Orders
                orders = stats.get('orders', {})
                text += f"📋 **Orders:**\n"
                text += f"• Total: {orders.get('total', 0)}\n"
                text += f"• Completed: {orders.get('completed', 0)}\n"
                text += f"• Success Rate: {orders.get('completion_rate', 0):.1f}%\n"
                
                await message.answer(text)
            break
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        await message.answer("❌ Error getting stats")

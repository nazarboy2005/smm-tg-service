"""
Settings management service for dynamic configuration
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from loguru import logger
import json

from bot.database.models import Setting
from bot.config import settings


class SettingsService:
    """Service for managing dynamic bot settings"""
    
    # Default settings that can be changed by admin
    DEFAULT_SETTINGS = {
        # Financial Settings
        "coins_per_usd": {"value": "10000", "type": "int", "description": "Coins per 1 USD"},
        "min_deposit_usd": {"value": "1.0", "type": "float", "description": "Minimum deposit in USD"},
        "max_deposit_usd": {"value": "1000.0", "type": "float", "description": "Maximum deposit in USD"},
        "welcome_bonus_coins": {"value": "100", "type": "int", "description": "Welcome bonus coins for new users"},
        
        # Referral Settings
        "default_referral_bonus": {"value": "10", "type": "int", "description": "Default referral bonus in coins"},
        "referral_tap_requirement": {"value": "5", "type": "int", "description": "Number of button taps required to complete referral"},
        "referral_system_enabled": {"value": "true", "type": "bool", "description": "Enable/disable referral system"},
        
        # Order Settings
        "max_orders_per_day": {"value": "50", "type": "int", "description": "Maximum orders per user per day"},
        "order_processing_enabled": {"value": "true", "type": "bool", "description": "Enable/disable order processing"},
        
        # Payment Settings
        "paypal_enabled": {"value": "true", "type": "bool", "description": "Enable PayPal payments"},
        "crypto_enabled": {"value": "true", "type": "bool", "description": "Enable crypto payments"},
        "payme_enabled": {"value": "true", "type": "bool", "description": "Enable Payme payments"},
        "click_enabled": {"value": "true", "type": "bool", "description": "Enable Click payments"},
        "uzcard_enabled": {"value": "false", "type": "bool", "description": "Enable Uzcard payments"},
        "humo_enabled": {"value": "false", "type": "bool", "description": "Enable Humo payments"},
        
        # Service Settings
        "auto_sync_services": {"value": "true", "type": "bool", "description": "Auto sync services from JAP API"},
        "service_sync_interval": {"value": "3600", "type": "int", "description": "Service sync interval in seconds"},
        "jap_services_enabled": {"value": "false", "type": "bool", "description": "Enable JAP service fetching and display (admin must enable this)"},
        
        # Bot Settings
        "maintenance_mode": {"value": "false", "type": "bool", "description": "Enable maintenance mode"},
        "new_user_registration": {"value": "true", "type": "bool", "description": "Allow new user registration"},
        "bot_welcome_message": {"value": "Welcome to SMM Bot!", "type": "str", "description": "Bot welcome message"},
        
        # Rate Limiting
        "rate_limit_messages": {"value": "30", "type": "int", "description": "Max messages per minute per user"},
        "rate_limit_orders": {"value": "10", "type": "int", "description": "Max orders per hour per user"},
        
        # Crypto Addresses
        "bitcoin_address": {"value": settings.bitcoin_address or "", "type": "str", "description": "Bitcoin wallet address"},
        "ethereum_address": {"value": settings.ethereum_address or "", "type": "str", "description": "Ethereum wallet address"},
        "solana_address": {"value": settings.solana_address or "", "type": "str", "description": "Solana wallet address"},
        "xrp_address": {"value": settings.xrp_address or "", "type": "str", "description": "XRP wallet address"},
        "doge_address": {"value": settings.doge_address or "", "type": "str", "description": "Dogecoin wallet address"},
        "toncoin_address": {"value": settings.toncoin_address or "", "type": "str", "description": "Toncoin wallet address"},
    }
    
    @staticmethod
    async def initialize_default_settings(db: AsyncSession) -> bool:
        """Initialize default settings in database"""
        try:
            for key, config in SettingsService.DEFAULT_SETTINGS.items():
                logger.debug(f"Processing setting: {key} = {config['value']} (type: {type(config['value'])})")
                # Check if setting already exists
                result = await db.execute(
                    select(Setting).where(Setting.key == key)
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    # Ensure value is always a string
                    value = str(config["value"]) if config["value"] is not None else ""
                    setting = Setting(
                        key=key,
                        value=value,
                        description=config["description"]
                    )
                    db.add(setting)
            
            await db.commit()
            logger.info("Default settings initialized")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error initializing default settings: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    @staticmethod
    async def get_setting(db: AsyncSession, key: str, default: Any = None) -> Any:
        """Get setting value with type conversion"""
        try:
            result = await db.execute(
                select(Setting).where(Setting.key == key)
            )
            setting = result.scalar_one_or_none()
            
            if not setting:
                return default
            
            # Get setting type from defaults
            setting_config = SettingsService.DEFAULT_SETTINGS.get(key, {"type": "str"})
            setting_type = setting_config["type"]
            
            # Convert value based on type
            if setting_type == "int":
                return int(setting.value)
            elif setting_type == "float":
                return float(setting.value)
            elif setting_type == "bool":
                return setting.value.lower() in ("true", "1", "yes", "on")
            else:
                return setting.value
                
        except Exception as e:
            logger.error(f"Error getting setting {key}: {e}")
            return default
    
    @staticmethod
    async def set_setting(db: AsyncSession, key: str, value: Any, admin_id: int) -> bool:
        """Set setting value"""
        try:
            # Validate setting exists in defaults
            if key not in SettingsService.DEFAULT_SETTINGS:
                logger.warning(f"Unknown setting key: {key}")
                return False
            
            # Convert value to string for storage
            str_value = str(value)
            
            # Get or create setting
            result = await db.execute(
                select(Setting).where(Setting.key == key)
            )
            setting = result.scalar_one_or_none()
            
            if setting:
                old_value = setting.value
                setting.value = str_value
            else:
                setting = Setting(
                    key=key,
                    value=str_value,
                    description=SettingsService.DEFAULT_SETTINGS[key]["description"]
                )
                db.add(setting)
                old_value = "None"
            
            await db.commit()
            
            logger.info(f"Admin {admin_id} changed setting {key}: {old_value} -> {str_value}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error setting {key}: {e}")
            return False
    
    @staticmethod
    async def get_all_settings(db) -> Dict[str, Dict[str, Any]]:
        """Get all settings with metadata"""
        try:
            # Use raw SQL query for asyncpg connection
            settings_db = await db.fetch("SELECT key, value, description FROM settings")
            
            settings_dict = {}
            
            # Add settings from database
            for setting in settings_db:
                config = SettingsService.DEFAULT_SETTINGS.get(setting['key'], {"type": "str"})
                settings_dict[setting['key']] = {
                    "value": setting['value'],
                    "type": config["type"],
                    "description": setting['description'] or config.get("description", ""),
                    "category": SettingsService._get_setting_category(setting['key'])
                }
            
            # Add missing default settings
            for key, config in SettingsService.DEFAULT_SETTINGS.items():
                if key not in settings_dict:
                    settings_dict[key] = {
                        "value": config["value"],
                        "type": config["type"],
                        "description": config["description"],
                        "category": SettingsService._get_setting_category(key)
                    }
            
            return settings_dict
            
        except Exception as e:
            logger.error(f"Error getting all settings: {e}")
            return {}
    
    @staticmethod
    def _get_setting_category(key: str) -> str:
        """Get setting category for organization"""
        if key.startswith(("coins_", "min_deposit", "max_deposit")):
            return "💰 Financial"
        elif key.startswith("referral_"):
            return "👥 Referral"
        elif key.startswith(("max_orders", "order_")):
            return "📋 Orders"
        elif key.endswith("_enabled") and any(x in key for x in ["crypto", "payme", "click", "uzcard", "humo"]):
            return "💳 Payments"
        elif key.startswith(("auto_sync", "service_")):
            return "📊 Services"
        elif key.startswith(("maintenance", "new_user", "bot_")):
            return "🤖 Bot"
        elif key.startswith("rate_limit"):
            return "🛡️ Security"
        elif key.endswith("_address"):
            return "₿ Crypto Wallets"
        else:
            return "⚙️ Other"
    
    @staticmethod
    async def get_settings_by_category(db) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Get settings organized by category"""
        try:
            all_settings = await SettingsService.get_all_settings(db)
            categorized = {}
            
            for key, setting_data in all_settings.items():
                category = setting_data["category"]
                if category not in categorized:
                    categorized[category] = {}
                categorized[category][key] = setting_data
            
            return categorized
            
        except Exception as e:
            logger.error(f"Error getting settings by category: {e}")
            return {}
    
    @staticmethod
    async def validate_setting_value(key: str, value: str) -> tuple[bool, str]:
        """Validate setting value"""
        try:
            if key not in SettingsService.DEFAULT_SETTINGS:
                return False, "Unknown setting"
            
            setting_config = SettingsService.DEFAULT_SETTINGS[key]
            setting_type = setting_config["type"]
            
            # Type validation
            if setting_type == "int":
                try:
                    int_val = int(value)
                    # Additional validation for specific settings
                    if key == "coins_per_usd" and int_val <= 0:
                        return False, "Coins per USD must be positive"
                    elif key in ["max_orders_per_day", "rate_limit_messages", "rate_limit_orders"] and int_val <= 0:
                        return False, "Value must be positive"
                except ValueError:
                    return False, "Must be a valid integer"
                    
            elif setting_type == "float":
                try:
                    float_val = float(value)
                    if key in ["min_deposit_usd", "max_deposit_usd"] and float_val <= 0:
                        return False, "Amount must be positive"
                except ValueError:
                    return False, "Must be a valid number"
                    
            elif setting_type == "bool":
                if value.lower() not in ("true", "false", "1", "0", "yes", "no", "on", "off"):
                    return False, "Must be true/false"
            
            # Address validation for crypto addresses
            if key.endswith("_address") and value:
                if not SettingsService._validate_crypto_address(key, value):
                    return False, "Invalid crypto address format"
            
            return True, "Valid"
            
        except Exception as e:
            logger.error(f"Error validating setting {key}: {e}")
            return False, "Validation error"
    
    @staticmethod
    def _validate_crypto_address(key: str, address: str) -> bool:
        """Basic crypto address validation"""
        if not address:
            return True  # Empty is allowed
        
        try:
            if key == "bitcoin_address":
                return (address.startswith(("1", "3", "bc1")) and 
                       len(address) >= 26 and len(address) <= 62)
            elif key == "ethereum_address":
                return (address.startswith("0x") and len(address) == 42 and 
                       all(c in "0123456789abcdefABCDEF" for c in address[2:]))
            elif key == "solana_address":
                return len(address) >= 32 and len(address) <= 44
            elif key in ["xrp_address", "doge_address", "toncoin_address"]:
                return len(address) >= 20 and len(address) <= 100
            
        except Exception:
            pass
        
        return True  # Default to valid for unknown formats
    
    @staticmethod
    async def reset_setting_to_default(db: AsyncSession, key: str, admin_id: int) -> bool:
        """Reset setting to default value"""
        try:
            if key not in SettingsService.DEFAULT_SETTINGS:
                return False
            
            default_value = SettingsService.DEFAULT_SETTINGS[key]["value"]
            return await SettingsService.set_setting(db, key, default_value, admin_id)
            
        except Exception as e:
            logger.error(f"Error resetting setting {key}: {e}")
            return False
    
    @staticmethod
    async def export_settings(db: AsyncSession) -> str:
        """Export all settings as JSON"""
        try:
            settings_dict = await SettingsService.get_all_settings(db)
            return json.dumps(settings_dict, indent=2)
        except Exception as e:
            logger.error(f"Error exporting settings: {e}")
            return "{}"
    
    @staticmethod
    async def get_current_financial_settings(db: AsyncSession) -> Dict[str, Any]:
        """Get current financial settings for easy access"""
        try:
            return {
                "coins_per_usd": await SettingsService.get_setting(db, "coins_per_usd", 10000),
                "min_deposit_usd": await SettingsService.get_setting(db, "min_deposit_usd", 1.0),
                "max_deposit_usd": await SettingsService.get_setting(db, "max_deposit_usd", 1000.0),
                "default_referral_bonus": await SettingsService.get_setting(db, "default_referral_bonus", 10),
                "welcome_bonus_coins": await SettingsService.get_setting(db, "welcome_bonus_coins", 100)
            }
        except Exception as e:
            logger.error(f"Error getting financial settings: {e}")
            return {
                "coins_per_usd": 10000,
                "min_deposit_usd": 1.0,
                "max_deposit_usd": 1000.0,
                "default_referral_bonus": 10,
                "welcome_bonus_coins": 100
            }

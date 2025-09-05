"""
User service for managing user operations with asyncpg database
"""
from typing import Optional, List, Dict, Any
from loguru import logger
from bot.database.db import db_manager
from bot.utils.i18n import Language
from bot.database.models import UserLanguage


class UserService:
    """Service for user operations"""
    
    @staticmethod
    def _map_db_language_to_enum(db_language: str) -> Language:
        """Map database language enum to our Language enum"""
        mapping = {
            "ENGLISH": Language.ENGLISH,
            "UZBEK": Language.UZBEK,
            "RUSSIAN": Language.RUSSIAN
        }
        return mapping.get(db_language, Language.ENGLISH)
    
    @staticmethod
    async def get_user_by_telegram_id(telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get user by telegram ID"""
        try:
            # Check if this is the admin user
            is_admin = telegram_id == 1377513530
            
            # Try to get user from database
            query = """
                SELECT u.id, u.telegram_id, u.username, u.first_name, u.last_name, 
                       u.language, u.is_admin, u.is_active, u.created_at,
                       COALESCE(b.coins, 0.0) as balance
                FROM users u
                LEFT JOIN balances b ON u.id = b.user_id
                WHERE u.telegram_id = $1
            """
            
            result = await db_manager.fetchrow(query, telegram_id)
            
            if result:
                # Convert database result to dict
                user_data = {
                    "id": result["id"],
                    "telegram_id": result["telegram_id"],
                    "username": result["username"],
                    "first_name": result["first_name"],
                    "last_name": result["last_name"],
                    "language": UserService._map_db_language_to_enum(result["language"]) if result["language"] else Language.ENGLISH,
                    "is_admin": result["is_admin"] or is_admin,  # Override with hardcoded admin check
                    "is_active": result["is_active"],
                    "balance": float(result["balance"]) if result["balance"] else 0.0,
                    "created_at": result["created_at"]
                }
                return user_data
            else:
                # User doesn't exist, return None to trigger creation
                return None
                
        except Exception as e:
            logger.error(f"Error getting user by telegram_id {telegram_id}: {e}")
            # Fallback to basic structure for admin
            if telegram_id == 1377513530:
                return {
                    "id": 1,
                    "telegram_id": telegram_id,
                    "username": "admin",
                    "language": Language.ENGLISH,
                    "balance": 0.0,
                    "is_admin": True
                }
            return None
    
    @staticmethod
    async def create_user(
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language: Language = Language.ENGLISH
    ) -> Optional[Dict[str, Any]]:
        """Create new user"""
        try:
            # Check if this is the admin user
            is_admin = telegram_id == 1377513530
            
            # Generate referral code
            import secrets
            referral_code = secrets.token_hex(4).upper()
            
            # Create user in database
            query = """
                INSERT INTO users (telegram_id, username, first_name, last_name, 
                                 language, is_admin, is_active, referral_code)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id, telegram_id, username, first_name, last_name, 
                         language, is_admin, is_active, created_at
            """
            
            result = await db_manager.fetchrow(
                query, 
                telegram_id, 
                username, 
                first_name, 
                last_name, 
                language.name.upper(), 
                is_admin, 
                True, 
                referral_code
            )
            
            if result:
                user_data = {
                    "id": result["id"],
                    "telegram_id": result["telegram_id"],
                    "username": result["username"],
                    "first_name": result["first_name"],
                    "last_name": result["last_name"],
                    "language": UserService._map_db_language_to_enum(result["language"]),
                    "is_admin": result["is_admin"],
                    "is_active": result["is_active"],
                    "balance": 0.0,  # New users start with 0 balance
                    "created_at": result["created_at"]
                }
                
                # Create initial balance record
                balance_query = """
                    INSERT INTO balances (user_id, coins, created_at, updated_at)
                    VALUES ($1, $2, NOW(), NOW())
                """
                await db_manager.execute(balance_query, result["id"], 0.0)
                
                logger.info(f"Created new user: {user_data['telegram_id']} with language {user_data['language']}")
                return user_data
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    @staticmethod
    async def update_user_language(telegram_id: int, language: Language) -> bool:
        """Update user language"""
        try:
            query = """
                UPDATE users 
                SET language = $1, updated_at = NOW()
                WHERE telegram_id = $2
            """
            
            result = await db_manager.execute(query, language.name.upper(), telegram_id)
            logger.info(f"Language updated for user {telegram_id} to {language}")
            return True
        except Exception as e:
            logger.error(f"Error updating user language: {e}")
            return False
    
    @staticmethod
    async def get_user_balance(telegram_id: int) -> float:
        """Get user balance"""
        try:
            query = """
                SELECT COALESCE(b.coins, 0.0) as balance
                FROM users u
                LEFT JOIN balances b ON u.id = b.user_id
                WHERE u.telegram_id = $1
            """
            
            result = await db_manager.fetchval(query, telegram_id)
            return float(result) if result is not None else 0.0
        except Exception as e:
            logger.error(f"Error getting user balance: {e}")
            return 0.0
    
    @staticmethod
    async def update_user_balance(telegram_id: int, amount: float) -> bool:
        """Update user balance"""
        try:
            # First, get the user ID
            user_query = "SELECT id FROM users WHERE telegram_id = $1"
            user_id = await db_manager.fetchval(user_query, telegram_id)
            
            if not user_id:
                logger.error(f"User not found for telegram_id: {telegram_id}")
                return False
            
            # Update or insert balance
            balance_query = """
                INSERT INTO balances (user_id, coins, created_at, updated_at)
                VALUES ($1, $2, NOW(), NOW())
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    coins = balances.coins + $2,
                    updated_at = NOW()
            """
            
            await db_manager.execute(balance_query, user_id, amount)
            logger.info(f"Balance updated for user {telegram_id} by {amount}")
            return True
        except Exception as e:
            logger.error(f"Error updating user balance: {e}")
            return False

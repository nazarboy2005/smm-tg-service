"""
User management service
"""
import secrets
import string
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload
from loguru import logger

from bot.database.models import User, Balance, UserLanguage, TransactionType, TransactionStatus
from bot.config import settings


class UserService:
    """Service for user management operations"""
    
    @staticmethod
    def generate_referral_code(user_id: int = None) -> str:
        """Generate unique referral code based on user ID for better tracking"""
        if user_id:
            # Create a code that includes user ID for better tracking
            # Format: 2 letters + user_id (padded to 6 digits) + 2 random chars
            user_id_str = str(user_id).zfill(6)
            prefix = ''.join(secrets.choice(string.ascii_uppercase) for _ in range(2))
            suffix = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(2))
            return f"{prefix}{user_id_str}{suffix}"
        else:
            # Fallback for backward compatibility
            return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
    
    @staticmethod
    async def get_user_by_telegram_id(db: AsyncSession, telegram_id: int, max_retries: int = 3) -> Optional[User]:
        """Get user by telegram ID"""
        for attempt in range(max_retries):
            try:
                result = await db.execute(
                    select(User)
                    .options(selectinload(User.balance))
                    .where(User.telegram_id == telegram_id)
                )
                return result.scalar_one_or_none()
            except Exception as e:
                logger.error(f"Error getting user by telegram_id {telegram_id} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return None
                # If we got a DuplicatePreparedStatementError, let's create a new session
                await db.close()
                db = AsyncSession(bind=db.get_bind())
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            result = await db.execute(
                select(User)
                .options(selectinload(User.balance))
                .where(User.id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by id {user_id}: {e}")
            return None
    
    @staticmethod
    async def get_user_by_referral_code(db: AsyncSession, referral_code: str) -> Optional[User]:
        """Get user by referral code"""
        try:
            result = await db.execute(
                select(User).where(User.referral_code == referral_code)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by referral_code {referral_code}: {e}")
            return None
    
    @staticmethod
    def extract_user_id_from_referral_code(referral_code: str) -> Optional[int]:
        """Extract user ID from referral code (format: 2 letters + 6 digits + 2 chars)"""
        try:
            if len(referral_code) == 10 and referral_code[2:8].isdigit():
                return int(referral_code[2:8])
            return None
        except (ValueError, IndexError):
            return None
    
    @staticmethod
    async def get_user_by_referral_code_or_id(db: AsyncSession, referral_code: str) -> Optional[User]:
        """Get user by referral code or extract user ID from referral code"""
        try:
            # First try direct referral code lookup
            user = await UserService.get_user_by_referral_code(db, referral_code)
            if user:
                return user
            
            # If not found, try to extract user ID from referral code
            user_id = UserService.extract_user_id_from_referral_code(referral_code)
            if user_id:
                return await UserService.get_user_by_id(db, user_id)
            
            return None
        except Exception as e:
            logger.error(f"Error getting user by referral_code_or_id {referral_code}: {e}")
            return None
    
    @staticmethod
    async def create_user(
        db: AsyncSession,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language: UserLanguage = UserLanguage.ENGLISH,
        referred_by_code: Optional[str] = None,
        max_retries: int = 3
    ) -> Optional[User]:
        """Create new user"""
        for attempt in range(max_retries):
            try:
                # Check if user already exists
                existing_user = await UserService.get_user_by_telegram_id(db, telegram_id)
                if existing_user:
                    return existing_user
                
                # If we got a DuplicatePreparedStatementError before, let's create a new session
                if attempt > 0:
                    await db.close()
                    db = AsyncSession(bind=db.get_bind())
                
                # Check if user is admin - ensure admin_ids is properly parsed
                try:
                    admin_ids = settings.admin_ids
                    if isinstance(admin_ids, str):
                        # Handle case where admin_ids might be a string
                        admin_ids = [int(id_.strip()) for id_ in admin_ids.split(',') if id_.strip().isdigit()]
                    elif not isinstance(admin_ids, list):
                        admin_ids = []
                    
                    is_admin = telegram_id in admin_ids
                except (ValueError, TypeError, AttributeError):
                    logger.warning(f"Error parsing admin_ids: {settings.admin_ids}, defaulting to False")
                    is_admin = False
                
                # Create user first to get the ID
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    language=language,
                    is_admin=is_admin,
                    referral_code="",  # Temporary, will be updated after we get the ID
                    referred_by=None  # Will be set after we find the referrer
                    )
                
                db.add(user)
                await db.flush()  # Get user.id
                
                # Generate unique referral code based on user ID
                referral_code = UserService.generate_referral_code(user.id)
                while await UserService.get_user_by_referral_code(db, referral_code):
                    referral_code = UserService.generate_referral_code(user.id)
                
                # Update user with the final referral code
                user.referral_code = referral_code
                
                # Find referrer if referral code provided
                referrer_id = None
                if referred_by_code:
                    referrer = await UserService.get_user_by_referral_code_or_id(db, referred_by_code)
                    if referrer:
                        referrer_id = referrer.id
                        user.referred_by = referrer_id
                        logger.info(f"User {telegram_id} referred by user {referrer_id} (code: {referred_by_code})")
                
                # Create balance with welcome bonus
                from bot.services.settings_service import SettingsService
                welcome_bonus = await SettingsService.get_setting(db, "welcome_bonus_coins", 100)
                balance = Balance(user_id=user.id, coins=float(welcome_bonus))
                db.add(balance)
                
                # Log welcome bonus
                if welcome_bonus > 0:
                    logger.info(f"Added welcome bonus of {welcome_bonus} coins to user {user.id}")
                
                # Create transaction record for the welcome bonus
                from bot.services.balance_service import BalanceService
                await BalanceService.add_transaction(
                    db=db,
                    user_id=user.id,
                    amount=float(welcome_bonus),
                    transaction_type=TransactionType.ADMIN_ADJUSTMENT,
                    description="Welcome bonus",
                    status=TransactionStatus.COMPLETED
                )
            
                await db.commit()
                
                # Reload user with balance
                await db.refresh(user)
                user.balance = balance
                
                logger.info(f"Created new user: {telegram_id} (username: {username})")
                return user
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error creating user {telegram_id} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return None
                # If we got an error, let's create a new session for the next attempt
                await db.close()
                db = AsyncSession(bind=db.get_bind())
        
        # If we reach here, all attempts failed
        return None
    
    @staticmethod
    async def update_user_language(db: AsyncSession, user_id: int, language: UserLanguage) -> bool:
        """Update user language"""
        try:
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(language=language)
            )
            await db.commit()
            logger.info(f"Updated language for user {user_id} to {language.value}")
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating language for user {user_id}: {e}")
            return False
    
    @staticmethod
    async def update_user_activity(db: AsyncSession, user_id: int) -> bool:
        """Update user last activity"""
        try:
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(last_activity=func.now())
            )
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating activity for user {user_id}: {e}")
            return False
    
    @staticmethod
    async def get_user_referrals(db: AsyncSession, user_id: int) -> List[User]:
        """Get users referred by this user"""
        try:
            result = await db.execute(
                select(User).where(User.referred_by == user_id)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting referrals for user {user_id}: {e}")
            return []
    
    @staticmethod
    async def get_user_stats(db: AsyncSession, user_id: int) -> dict:
        """Get user statistics"""
        try:
            user = await UserService.get_user_by_id(db, user_id)
            if not user:
                return {}
            
            referrals = await UserService.get_user_referrals(db, user_id)
            
            # Get total referral earnings (this would be implemented with transaction service)
            referral_earnings = 0.0  # Placeholder
            
            return {
                "balance": user.balance.coins if user.balance else 0.0,
                "referrals_count": len(referrals),
                "referral_earnings": referral_earnings,
                "total_orders": 0,  # Placeholder - would be calculated from orders
                "is_admin": user.is_admin
            }
        except Exception as e:
            logger.error(f"Error getting stats for user {user_id}: {e}")
            return {}
    
    @staticmethod
    async def get_all_users(
        db: AsyncSession, 
        offset: int = 0, 
        limit: int = 50
    ) -> List[User]:
        """Get all users with pagination"""
        try:
            result = await db.execute(
                select(User)
                .options(selectinload(User.balance))
                .offset(offset)
                .limit(limit)
                .order_by(User.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    @staticmethod
    async def get_users_count(db: AsyncSession) -> int:
        """Get total users count"""
        try:
            result = await db.execute(select(func.count(User.id)))
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error getting users count: {e}")
            return 0
    
    @staticmethod
    async def search_users(
        db: AsyncSession, 
        query: str, 
        offset: int = 0, 
        limit: int = 50
    ) -> List[User]:
        """Search users by username or name"""
        try:
            search_pattern = f"%{query}%"
            result = await db.execute(
                select(User)
                .options(selectinload(User.balance))
                .where(
                    (User.username.ilike(search_pattern)) |
                    (User.first_name.ilike(search_pattern)) |
                    (User.last_name.ilike(search_pattern))
                )
                .offset(offset)
                .limit(limit)
                .order_by(User.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error searching users with query '{query}': {e}")
            return []
    
    @staticmethod
    async def get_referral_stats(db: AsyncSession, user_id: int) -> dict:
        """Get detailed referral statistics for a user"""
        try:
            user = await UserService.get_user_by_id(db, user_id)
            if not user:
                return {}
            
            # Get direct referrals
            direct_referrals = await UserService.get_user_referrals(db, user_id)
            
            # Get referral earnings (would be calculated from transactions)
            # This is a placeholder - implement with transaction service
            referral_earnings = 0.0
            
            # Get referral chain depth (how many levels deep)
            referral_chain = await UserService.get_referral_chain(db, user_id)
            
            return {
                "user_id": user_id,
                "referral_code": user.referral_code,
                "direct_referrals_count": len(direct_referrals),
                "total_referrals_count": len(referral_chain),
                "referral_earnings": referral_earnings,
                "referral_chain_depth": len(referral_chain),
                "direct_referrals": [
                    {
                        "id": ref.id,
                        "telegram_id": ref.telegram_id,
                        "username": ref.username,
                        "first_name": ref.first_name,
                        "created_at": ref.created_at.isoformat() if ref.created_at else None
                    }
                    for ref in direct_referrals
                ]
            }
        except Exception as e:
            logger.error(f"Error getting referral stats for user {user_id}: {e}")
            return {}
    
    @staticmethod
    async def get_referral_chain(db: AsyncSession, user_id: int, max_depth: int = 5) -> List[User]:
        """Get complete referral chain for a user (recursive)"""
        try:
            chain = []
            visited = set()
            
            async def get_chain_recursive(current_user_id: int, depth: int = 0):
                if depth >= max_depth or current_user_id in visited:
                    return
                
                visited.add(current_user_id)
                referrals = await UserService.get_user_referrals(db, current_user_id)
                
                for referral in referrals:
                    if referral.id not in visited:
                        chain.append(referral)
                        await get_chain_recursive(referral.id, depth + 1)
            
            await get_chain_recursive(user_id)
            return chain
        except Exception as e:
            logger.error(f"Error getting referral chain for user {user_id}: {e}")
            return []
    
    @staticmethod
    async def update_user_profile(
        db: AsyncSession,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> bool:
        """Update user profile information"""
        try:
            update_data = {}
            if username is not None:
                update_data['username'] = username
            if first_name is not None:
                update_data['first_name'] = first_name
            if last_name is not None:
                update_data['last_name'] = last_name
            
            if update_data:
                await db.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(**update_data)
                )
                await db.commit()
                logger.info(f"Updated profile for user {user_id}")
                return True
            
            return False
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating profile for user {user_id}: {e}")
            return False
    
    @staticmethod
    async def deactivate_user(db: AsyncSession, user_id: int) -> bool:
        """Deactivate a user account"""
        try:
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(is_active=False)
            )
            await db.commit()
            logger.info(f"Deactivated user {user_id}")
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deactivating user {user_id}: {e}")
            return False
    
    @staticmethod
    async def reactivate_user(db: AsyncSession, user_id: int) -> bool:
        """Reactivate a user account"""
        try:
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(is_active=True)
            )
            await db.commit()
            logger.info(f"Reactivated user {user_id}")
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Error reactivating user {user_id}: {e}")
            return False

"""
Referral system service
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from loguru import logger

from bot.database.models import (
    User, ReferralReward, ReferralButtonTap, Transaction, TransactionType, TransactionStatus
)
from bot.services.balance_service import BalanceService
from bot.services.settings_service import SettingsService
from bot.config import settings


class ReferralService:
    """Service for referral system management"""
    
    @staticmethod
    async def process_referral_signup(
        db: AsyncSession,
        referrer_id: int,
        referred_user_id: int
    ) -> Optional[ReferralReward]:
        """Process referral signup and create reward"""
        try:
            # Validate that referrer and referred are different users
            if referrer_id == referred_user_id:
                logger.warning(f"User {referrer_id} tried to refer themselves")
                return None
            
            # Check if reward already exists
            existing_reward = await db.execute(
                select(ReferralReward).where(
                    (ReferralReward.referrer_id == referrer_id) &
                    (ReferralReward.referred_id == referred_user_id)
                )
            )
            if existing_reward.scalar_one_or_none():
                logger.info(f"Referral reward already exists for referrer {referrer_id} and referred {referred_user_id}")
                return None
            
            # Get referral settings
            referral_bonus = await SettingsService.get_setting(db, "default_referral_bonus", 10)
            button_taps_required = await SettingsService.get_setting(db, "referral_tap_requirement", 5)
            
            # Create referral reward record
            reward = ReferralReward(
                referrer_id=referrer_id,
                referred_id=referred_user_id,
                reward_amount=referral_bonus,
                is_paid=False,
                button_taps=0,
                button_taps_required=button_taps_required,
                is_completed=False
            )
            
            db.add(reward)
            await db.commit()
            
            logger.info(f"Created referral reward: referrer {referrer_id}, referred {referred_user_id}, amount {referral_bonus}, taps required: {button_taps_required}")
            return reward
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error processing referral signup: {e}")
            return None
    
    @staticmethod
    async def pay_referral_bonus(
        db: AsyncSession,
        reward_id: int
    ) -> bool:
        """Pay referral bonus to referrer"""
        try:
            # Get referral reward
            result = await db.execute(
                select(ReferralReward).where(ReferralReward.id == reward_id)
            )
            reward = result.scalar_one_or_none()
            
            if not reward:
                logger.warning(f"Referral reward {reward_id} not found")
                return False
            
            if reward.is_paid:
                logger.info(f"Referral reward {reward_id} already paid")
                return True
            
            # Add balance to referrer
            transaction = await BalanceService.add_balance(
                db=db,
                user_id=reward.referrer_id,
                amount=reward.reward_amount,
                transaction_type=TransactionType.REFERRAL_BONUS,
                description=f"Referral bonus for user #{reward.referred_id}",
                metadata={"referral_reward_id": reward_id, "referred_user_id": reward.referred_id}
            )
            
            if transaction:
                # Mark reward as paid
                reward.is_paid = True
                reward.transaction_id = transaction.id
                await db.commit()
                
                logger.info(f"Paid referral bonus: {reward.reward_amount} coins to user {reward.referrer_id}")
                return True
            
            return False
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error paying referral bonus {reward_id}: {e}")
            return False
    
    @staticmethod
    async def record_button_tap(
        db: AsyncSession,
        user_id: int,
        button_type: str
    ) -> bool:
        """Record a button tap for referral tracking"""
        try:
            # Get user
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user or not user.referred_by:
                return False
            
            # Check if there's a referral reward
            reward_result = await db.execute(
                select(ReferralReward).where(
                    (ReferralReward.referrer_id == user.referred_by) &
                    (ReferralReward.referred_id == user_id) &
                    (ReferralReward.is_completed == False)
                )
            )
            reward = reward_result.scalar_one_or_none()
            
            if not reward:
                return False
            
            # Record the button tap
            button_tap = ReferralButtonTap(
                user_id=user_id,
                referral_reward_id=reward.id,
                button_type=button_type
            )
            db.add(button_tap)
            
            # Increment the button tap count
            reward.button_taps += 1
            
            # Check if referral is completed
            if reward.button_taps >= reward.button_taps_required:
                reward.is_completed = True
                
                # Pay the referral bonus if completed
                if not reward.is_paid:
                    await ReferralService.pay_referral_bonus(db, reward.id)
            
            await db.commit()
            logger.info(f"Recorded button tap for user {user_id}, type: {button_type}, taps: {reward.button_taps}/{reward.button_taps_required}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error recording button tap for user {user_id}: {e}")
            return False
    
    @staticmethod
    async def get_referral_progress(
        db: AsyncSession,
        user_id: int
    ) -> Dict[str, Any]:
        """Get referral progress for a user"""
        try:
            # Get user
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user or not user.referred_by:
                return {
                    "has_referrer": False,
                    "button_taps": 0,
                    "button_taps_required": 5,
                    "is_completed": False,
                    "progress_percentage": 0
                }
            
            # Get referral reward
            reward_result = await db.execute(
                select(ReferralReward).where(
                    (ReferralReward.referrer_id == user.referred_by) &
                    (ReferralReward.referred_id == user_id)
                )
            )
            reward = reward_result.scalar_one_or_none()
            
            if not reward:
                return {
                    "has_referrer": True,
                    "button_taps": 0,
                    "button_taps_required": 5,
                    "is_completed": False,
                    "progress_percentage": 0
                }
            
            # Calculate progress
            progress_percentage = min(100, int((reward.button_taps / reward.button_taps_required) * 100))
            
            return {
                "has_referrer": True,
                "button_taps": reward.button_taps,
                "button_taps_required": reward.button_taps_required,
                "is_completed": reward.is_completed,
                "is_paid": reward.is_paid,
                "progress_percentage": progress_percentage
            }
            
        except Exception as e:
            logger.error(f"Error getting referral progress for user {user_id}: {e}")
            return {
                "has_referrer": False,
                "button_taps": 0,
                "button_taps_required": 5,
                "is_completed": False,
                "progress_percentage": 0
            }
    
    @staticmethod
    async def trigger_referral_activity(
        db: AsyncSession,
        user_id: int,
        activity_type: str = "first_order"
    ) -> bool:
        """Trigger referral bonus when referred user becomes active"""
        try:
            # Get user
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user or not user.referred_by:
                return False
            
            # Check if there's an unpaid referral reward
            reward_result = await db.execute(
                select(ReferralReward).where(
                    (ReferralReward.referrer_id == user.referred_by) &
                    (ReferralReward.referred_id == user_id) &
                    (ReferralReward.is_paid == False) &
                    (ReferralReward.is_completed == True)
                )
            )
            reward = reward_result.scalar_one_or_none()
            
            if reward:
                # Pay the referral bonus
                success = await ReferralService.pay_referral_bonus(db, reward.id)
                if success:
                    logger.info(f"Triggered referral bonus payment for user {user_id} activity: {activity_type}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error triggering referral activity for user {user_id}: {e}")
            return False
    
    @staticmethod
    async def get_user_referral_stats(db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """Get referral statistics for user"""
        try:
            # Get referrals count
            referrals_result = await db.execute(
                select(func.count(User.id)).where(User.referred_by == user_id)
            )
            referrals_count = referrals_result.scalar() or 0
            
            # Get total earnings from referrals
            earnings_result = await db.execute(
                select(func.sum(ReferralReward.reward_amount))
                .where(
                    (ReferralReward.referrer_id == user_id) &
                    (ReferralReward.is_paid == True)
                )
            )
            total_earnings = earnings_result.scalar() or 0.0
            
            # Get pending rewards
            pending_result = await db.execute(
                select(func.sum(ReferralReward.reward_amount))
                .where(
                    (ReferralReward.referrer_id == user_id) &
                    (ReferralReward.is_paid == False)
                )
            )
            pending_earnings = pending_result.scalar() or 0.0
            
            return {
                "referrals_count": referrals_count,
                "total_earnings": total_earnings,
                "pending_earnings": pending_earnings,
                "bonus_per_referral": settings.default_referral_bonus
            }
            
        except Exception as e:
            logger.error(f"Error getting referral stats for user {user_id}: {e}")
            return {
                "referrals_count": 0,
                "total_earnings": 0.0,
                "pending_earnings": 0.0,
                "bonus_per_referral": settings.default_referral_bonus
            }
    
    @staticmethod
    async def get_referral_link(bot_username: str, referral_code: str) -> str:
        """Generate referral link for user"""
        return f"https://t.me/{bot_username}?start=ref_{referral_code}"
    
    @staticmethod
    async def get_referral_link_by_user_id(bot_username: str, user_id: int) -> str:
        """Generate referral link using user ID (for backward compatibility)"""
        return f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    @staticmethod
    async def get_user_referrals(
        db: AsyncSession,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[User]:
        """Get list of users referred by this user"""
        try:
            result = await db.execute(
                select(User)
                .where(User.referred_by == user_id)
                .order_by(User.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting referrals for user {user_id}: {e}")
            return []
    
    @staticmethod
    async def get_top_referrers(
        db: AsyncSession,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top referrers by number of referrals"""
        try:
            result = await db.execute(
                select(
                    User.id,
                    User.username,
                    User.first_name,
                    func.count(User.id.distinct()).label('referrals_count')
                )
                .join(User, User.referred_by == User.id, isouter=True)
                .group_by(User.id, User.username, User.first_name)
                .having(func.count(User.id.distinct()) > 0)
                .order_by(func.count(User.id.distinct()).desc())
                .limit(limit)
            )
            
            top_referrers = []
            for row in result:
                top_referrers.append({
                    "user_id": row.id,
                    "username": row.username,
                    "first_name": row.first_name,
                    "referrals_count": row.referrals_count
                })
            
            return top_referrers
            
        except Exception as e:
            logger.error(f"Error getting top referrers: {e}")
            return []
    
    @staticmethod
    async def get_referral_rewards_summary(db: AsyncSession) -> Dict[str, Any]:
        """Get referral rewards summary for admin"""
        try:
            # Total rewards paid
            paid_result = await db.execute(
                select(
                    func.count(ReferralReward.id),
                    func.sum(ReferralReward.reward_amount)
                )
                .where(ReferralReward.is_paid == True)
            )
            paid_count, paid_amount = paid_result.first() or (0, 0.0)
            
            # Total rewards pending
            pending_result = await db.execute(
                select(
                    func.count(ReferralReward.id),
                    func.sum(ReferralReward.reward_amount)
                )
                .where(ReferralReward.is_paid == False)
            )
            pending_count, pending_amount = pending_result.first() or (0, 0.0)
            
            return {
                "paid_rewards_count": paid_count or 0,
                "paid_rewards_amount": paid_amount or 0.0,
                "pending_rewards_count": pending_count or 0,
                "pending_rewards_amount": pending_amount or 0.0,
                "total_rewards_count": (paid_count or 0) + (pending_count or 0),
                "total_rewards_amount": (paid_amount or 0.0) + (pending_amount or 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error getting referral rewards summary: {e}")
            return {
                "paid_rewards_count": 0,
                "paid_rewards_amount": 0.0,
                "pending_rewards_count": 0,
                "pending_rewards_amount": 0.0,
                "total_rewards_count": 0,
                "total_rewards_amount": 0.0
            }
    
    @staticmethod
    async def resolve_referral_code(db: AsyncSession, referral_code: str) -> Optional[int]:
        """Resolve referral code to user ID - handles both new format and legacy user IDs"""
        try:
            # First try to find user by referral code
            from bot.services.user_service import UserService
            user = await UserService.get_user_by_referral_code(db, referral_code)
            if user:
                return user.id
            
            # If not found, try to extract user ID from referral code format
            user_id = UserService.extract_user_id_from_referral_code(referral_code)
            if user_id:
                # Verify the user exists
                user = await UserService.get_user_by_id(db, user_id)
                if user:
                    return user_id
            
            # If still not found, try to treat referral_code as a direct user ID
            try:
                potential_user_id = int(referral_code)
                user = await UserService.get_user_by_id(db, potential_user_id)
                if user:
                    return potential_user_id
            except (ValueError, TypeError):
                pass
            
            return None
        except Exception as e:
            logger.error(f"Error resolving referral code {referral_code}: {e}")
            return None

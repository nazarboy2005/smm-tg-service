"""
Admin service for management operations
"""
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy.orm import selectinload
from loguru import logger
from datetime import datetime, timedelta

from bot.database.models import (
    User, Balance, Transaction, Order, Service, ServiceCategory,
    Setting, ReferralReward, TransactionType, TransactionStatus, OrderStatus
)
from bot.services.balance_service import BalanceService
from bot.services.referral_service import ReferralService
from bot.services.service_service import ServiceService
from bot.services.order_service import OrderService


class AdminService:
    """Service for admin operations"""
    
    @staticmethod
    async def get_dashboard_stats(db: AsyncSession) -> Dict[str, Any]:
        """Get admin dashboard statistics"""
        try:
            # User stats
            total_users_result = await db.execute(select(func.count(User.id)))
            total_users = total_users_result.scalar() or 0
            
            # Active users (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            active_users_result = await db.execute(
                select(func.count(User.id.distinct()))
                .where(User.last_activity >= week_ago)
            )
            active_users = active_users_result.scalar() or 0
            
            # New users today
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            new_users_result = await db.execute(
                select(func.count(User.id))
                .where(User.created_at >= today)
            )
            new_users_today = new_users_result.scalar() or 0
            
            # Financial stats
            total_deposits = await BalanceService.get_total_deposits(db)
            
            # Total balance in system
            total_balance_result = await db.execute(select(func.sum(Balance.coins)))
            total_balance_coins = total_balance_result.scalar() or 0.0
            
            # Order stats
            total_orders_result = await db.execute(select(func.count(Order.id)))
            total_orders = total_orders_result.scalar() or 0
            
            completed_orders_result = await db.execute(
                select(func.count(Order.id))
                .where(Order.status == OrderStatus.COMPLETED)
            )
            completed_orders = completed_orders_result.scalar() or 0
            
            # Revenue from orders
            revenue_result = await db.execute(
                select(func.sum(Order.charge))
                .where(Order.status.in_([OrderStatus.COMPLETED, OrderStatus.PARTIAL]))
            )
            total_revenue_coins = revenue_result.scalar() or 0.0
            
            # Referral stats
            referral_stats = await ReferralService.get_referral_rewards_summary(db)
            
            # Service stats
            service_stats = await ServiceService.get_services_stats(db)
            
            return {
                "users": {
                    "total": total_users,
                    "active_week": active_users,
                    "new_today": new_users_today,
                    "growth_rate": round((new_users_today / max(total_users - new_users_today, 1)) * 100, 2)
                },
                "financial": {
                    "total_deposits_usd": total_deposits,
                    "total_deposits_coins": BalanceService.usd_to_coins(total_deposits),
                    "total_balance_coins": total_balance_coins,
                    "total_balance_usd": BalanceService.coins_to_usd(total_balance_coins),
                    "total_revenue_coins": total_revenue_coins,
                    "total_revenue_usd": BalanceService.coins_to_usd(total_revenue_coins)
                },
                "orders": {
                    "total": total_orders,
                    "completed": completed_orders,
                    "completion_rate": round((completed_orders / max(total_orders, 1)) * 100, 2)
                },
                "referrals": referral_stats,
                "services": service_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {}
    
    @staticmethod
    async def get_users_list(
        db: AsyncSession,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[User], int]:
        """Get paginated users list"""
        try:
            offset = (page - 1) * per_page
            
            # Build query
            query = select(User).options(selectinload(User.balance))
            
            # Add search filter
            if search:
                search_pattern = f"%{search}%"
                query = query.where(
                    or_(
                        User.username.ilike(search_pattern),
                        User.first_name.ilike(search_pattern),
                        User.last_name.ilike(search_pattern),
                        User.telegram_id.like(search_pattern)
                    )
                )
            
            # Add sorting
            sort_column = getattr(User, sort_by, User.created_at)
            if sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(sort_column)
            
            # Get total count
            count_query = select(func.count(User.id))
            if search:
                count_query = count_query.where(
                    or_(
                        User.username.ilike(search_pattern),
                        User.first_name.ilike(search_pattern),
                        User.last_name.ilike(search_pattern),
                        User.telegram_id.like(search_pattern)
                    )
                )
            
            total_result = await db.execute(count_query)
            total_count = total_result.scalar() or 0
            
            # Get users
            query = query.offset(offset).limit(per_page)
            result = await db.execute(query)
            users = result.scalars().all()
            
            return users, total_count
            
        except Exception as e:
            logger.error(f"Error getting users list: {e}")
            return [], 0
    
    @staticmethod
    async def get_user_details(db: AsyncSession, user_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed user information"""
        try:
            # Get user
            user_result = await db.execute(
                select(User)
                .options(selectinload(User.balance))
                .where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return None
            
            # Get user statistics
            stats = await AdminService._get_user_statistics(db, user_id)
            
            # Get recent transactions
            transactions = await BalanceService.get_user_transactions(db, user_id, limit=10)
            
            # Get recent orders
            orders = await OrderService.get_user_orders(db, user_id, limit=10)
            
            # Get referral info
            referral_stats = await ReferralService.get_user_referral_stats(db, user_id)
            
            return {
                "user": user,
                "stats": stats,
                "transactions": transactions,
                "orders": orders,
                "referrals": referral_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting user details {user_id}: {e}")
            return None
    
    @staticmethod
    async def _get_user_statistics(db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            # Total deposits
            deposits_result = await db.execute(
                select(func.sum(Transaction.usd_amount))
                .where(
                    and_(
                        Transaction.user_id == user_id,
                        Transaction.type == TransactionType.DEPOSIT,
                        Transaction.status == TransactionStatus.COMPLETED
                    )
                )
            )
            total_deposits = deposits_result.scalar() or 0.0
            
            # Total orders
            orders_result = await db.execute(
                select(func.count(Order.id))
                .where(Order.user_id == user_id)
            )
            total_orders = orders_result.scalar() or 0
            
            # Total spent on orders
            spent_result = await db.execute(
                select(func.sum(Order.charge))
                .where(Order.user_id == user_id)
            )
            total_spent = spent_result.scalar() or 0.0
            
            return {
                "total_deposits_usd": total_deposits,
                "total_orders": total_orders,
                "total_spent_coins": total_spent,
                "total_spent_usd": BalanceService.coins_to_usd(total_spent)
            }
            
        except Exception as e:
            logger.error(f"Error getting user statistics {user_id}: {e}")
            return {}
    
    @staticmethod
    async def adjust_user_balance(
        db: AsyncSession,
        user_id: int,
        amount: float,
        reason: str,
        admin_id: int
    ) -> bool:
        """Adjust user balance (admin operation)"""
        try:
            if amount > 0:
                # Add balance
                transaction = await BalanceService.add_balance(
                    db=db,
                    user_id=user_id,
                    amount=amount,
                    transaction_type=TransactionType.ADMIN_ADJUSTMENT,
                    description=f"Admin adjustment: {reason}",
                    metadata={"admin_id": admin_id, "reason": reason}
                )
            else:
                # Deduct balance
                transaction = await BalanceService.deduct_balance(
                    db=db,
                    user_id=user_id,
                    amount=abs(amount),
                    transaction_type=TransactionType.ADMIN_ADJUSTMENT,
                    description=f"Admin adjustment: {reason}",
                    metadata={"admin_id": admin_id, "reason": reason}
                )
            
            if transaction:
                logger.info(f"Admin {admin_id} adjusted user {user_id} balance by {amount} coins: {reason}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error adjusting user balance: {e}")
            return False
    
    @staticmethod
    async def get_transactions_list(
        db: AsyncSession,
        page: int = 1,
        per_page: int = 50,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None
    ) -> Tuple[List[Transaction], int]:
        """Get paginated transactions list"""
        try:
            offset = (page - 1) * per_page
            
            # Build query
            query = select(Transaction).options(selectinload(Transaction.user))
            
            # Add filters
            if transaction_type:
                query = query.where(Transaction.type == transaction_type)
            if status:
                query = query.where(Transaction.status == status)
            
            # Get total count
            count_query = select(func.count(Transaction.id))
            if transaction_type:
                count_query = count_query.where(Transaction.type == transaction_type)
            if status:
                count_query = count_query.where(Transaction.status == status)
            
            total_result = await db.execute(count_query)
            total_count = total_result.scalar() or 0
            
            # Get transactions
            query = query.order_by(desc(Transaction.created_at)).offset(offset).limit(per_page)
            result = await db.execute(query)
            transactions = result.scalars().all()
            
            return transactions, total_count
            
        except Exception as e:
            logger.error(f"Error getting transactions list: {e}")
            return [], 0
    
    @staticmethod
    async def get_orders_list(
        db: AsyncSession,
        page: int = 1,
        per_page: int = 50,
        status: Optional[OrderStatus] = None,
        service_id: Optional[int] = None
    ) -> Tuple[List[Order], int]:
        """Get paginated orders list"""
        try:
            offset = (page - 1) * per_page
            
            # Build query
            query = select(Order).options(
                selectinload(Order.user),
                selectinload(Order.service).selectinload(Service.category)
            )
            
            # Add filters
            if status:
                query = query.where(Order.status == status)
            if service_id:
                query = query.where(Order.service_id == service_id)
            
            # Get total count
            count_query = select(func.count(Order.id))
            if status:
                count_query = count_query.where(Order.status == status)
            if service_id:
                count_query = count_query.where(Order.service_id == service_id)
            
            total_result = await db.execute(count_query)
            total_count = total_result.scalar() or 0
            
            # Get orders
            query = query.order_by(desc(Order.created_at)).offset(offset).limit(per_page)
            result = await db.execute(query)
            orders = result.scalars().all()
            
            return orders, total_count
            
        except Exception as e:
            logger.error(f"Error getting orders list: {e}")
            return [], 0
    
    @staticmethod
    async def get_setting(db: AsyncSession, key: str) -> Optional[str]:
        """Get setting value"""
        try:
            result = await db.execute(
                select(Setting.value).where(Setting.key == key)
            )
            return result.scalar()
        except Exception as e:
            logger.error(f"Error getting setting {key}: {e}")
            return None
    
    @staticmethod
    async def set_setting(
        db: AsyncSession,
        key: str,
        value: str,
        description: Optional[str] = None
    ) -> bool:
        """Set setting value"""
        try:
            # Check if setting exists
            result = await db.execute(
                select(Setting).where(Setting.key == key)
            )
            setting = result.scalar_one_or_none()
            
            if setting:
                # Update existing
                setting.value = value
                if description:
                    setting.description = description
            else:
                # Create new
                setting = Setting(
                    key=key,
                    value=value,
                    description=description
                )
                db.add(setting)
            
            await db.commit()
            logger.info(f"Updated setting {key} = {value}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error setting {key}: {e}")
            return False
    
    @staticmethod
    async def get_analytics_data(
        db: AsyncSession,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics data for specified period"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Daily user registrations
            registrations_result = await db.execute(
                select(
                    func.date(User.created_at).label('date'),
                    func.count(User.id).label('count')
                )
                .where(User.created_at >= start_date)
                .group_by(func.date(User.created_at))
                .order_by(func.date(User.created_at))
            )
            registrations = [{"date": str(row.date), "count": row.count} for row in registrations_result]
            
            # Daily deposits
            deposits_result = await db.execute(
                select(
                    func.date(Transaction.created_at).label('date'),
                    func.sum(Transaction.usd_amount).label('amount')
                )
                .where(
                    and_(
                        Transaction.created_at >= start_date,
                        Transaction.type == TransactionType.DEPOSIT,
                        Transaction.status == TransactionStatus.COMPLETED
                    )
                )
                .group_by(func.date(Transaction.created_at))
                .order_by(func.date(Transaction.created_at))
            )
            deposits = [{"date": str(row.date), "amount": float(row.amount or 0)} for row in deposits_result]
            
            # Daily orders
            orders_result = await db.execute(
                select(
                    func.date(Order.created_at).label('date'),
                    func.count(Order.id).label('count'),
                    func.sum(Order.charge).label('revenue')
                )
                .where(Order.created_at >= start_date)
                .group_by(func.date(Order.created_at))
                .order_by(func.date(Order.created_at))
            )
            orders = [
                {
                    "date": str(row.date),
                    "count": row.count,
                    "revenue_coins": float(row.revenue or 0),
                    "revenue_usd": BalanceService.coins_to_usd(float(row.revenue or 0))
                }
                for row in orders_result
            ]
            
            return {
                "period_days": days,
                "registrations": registrations,
                "deposits": deposits,
                "orders": orders
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics data: {e}")
            return {}
    
    @staticmethod
    async def export_users_csv(db: AsyncSession) -> str:
        """Export users to CSV format"""
        try:
            users, _ = await AdminService.get_users_list(db, page=1, per_page=10000)
            
            csv_lines = ["ID,Telegram ID,Username,First Name,Last Name,Language,Balance,Created At,Last Activity"]
            
            for user in users:
                balance = user.balance.coins if user.balance else 0
                csv_lines.append(
                    f"{user.id},{user.telegram_id},{user.username or ''},"
                    f"{user.first_name or ''},{user.last_name or ''},{user.language.value},"
                    f"{balance},{user.created_at},{user.last_activity}"
                )
            
            return "\n".join(csv_lines)
            
        except Exception as e:
            logger.error(f"Error exporting users CSV: {e}")
            return ""

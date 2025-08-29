"""
Balance and transaction management service
"""
from typing import Optional, List, Dict, Any
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, desc
from sqlalchemy.orm import selectinload
from loguru import logger
import json

from bot.database.models import (
    User, Balance, Transaction, TransactionType, 
    TransactionStatus, PaymentMethod
)
from bot.config import settings
from bot.services.settings_service import SettingsService


class BalanceService:
    """Service for balance and transaction management"""
    
    @staticmethod
    async def get_user_balance(db: AsyncSession, user_id: int) -> float:
        """Get user balance in coins"""
        try:
            result = await db.execute(
                select(Balance.coins).where(Balance.user_id == user_id)
            )
            balance = result.scalar()
            return balance or 0.0
        except Exception as e:
            logger.error(f"Error getting balance for user {user_id}: {e}")
            return 0.0
    
    @staticmethod
    async def add_balance(
        db: AsyncSession,
        user_id: int,
        amount: float,
        transaction_type: TransactionType = TransactionType.DEPOSIT,
        payment_method: Optional[PaymentMethod] = None,
        external_id: Optional[str] = None,
        description: Optional[str] = None,
        usd_amount: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Transaction]:
        """Add balance to user account"""
        try:
            # Start transaction
            async with db.begin():
                # Get current balance
                result = await db.execute(
                    select(Balance).where(Balance.user_id == user_id).with_for_update()
                )
                balance = result.scalar_one_or_none()
                
                if not balance:
                    # Create balance if doesn't exist
                    balance = Balance(user_id=user_id, coins=0.0)
                    db.add(balance)
                    await db.flush()
                
                # Update balance
                new_balance = balance.coins + amount
                await db.execute(
                    update(Balance)
                    .where(Balance.user_id == user_id)
                    .values(coins=new_balance)
                )
                
                # Create transaction record
                transaction = Transaction(
                    user_id=user_id,
                    type=transaction_type,
                    status=TransactionStatus.COMPLETED,
                    amount=amount,
                    usd_amount=usd_amount,
                    payment_method=payment_method,
                    external_id=external_id,
                    description=description,
                    metadata=json.dumps(metadata) if metadata else None
                )
                
                db.add(transaction)
                await db.flush()
                
                logger.info(f"Added {amount} coins to user {user_id} balance (new balance: {new_balance})")
                return transaction
                
        except Exception as e:
            logger.error(f"Error adding balance for user {user_id}: {e}")
            return None
    
    @staticmethod
    async def deduct_balance(
        db: AsyncSession,
        user_id: int,
        amount: float,
        transaction_type: TransactionType = TransactionType.ORDER_PAYMENT,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Transaction]:
        """Deduct balance from user account"""
        try:
            # Start transaction
            async with db.begin():
                # Get current balance with lock
                result = await db.execute(
                    select(Balance).where(Balance.user_id == user_id).with_for_update()
                )
                balance = result.scalar_one_or_none()
                
                if not balance or balance.coins < amount:
                    logger.warning(f"Insufficient balance for user {user_id}: required {amount}, available {balance.coins if balance else 0}")
                    return None
                
                # Update balance
                new_balance = balance.coins - amount
                await db.execute(
                    update(Balance)
                    .where(Balance.user_id == user_id)
                    .values(coins=new_balance)
                )
                
                # Create transaction record
                transaction = Transaction(
                    user_id=user_id,
                    type=transaction_type,
                    status=TransactionStatus.COMPLETED,
                    amount=-amount,  # Negative for deductions
                    description=description,
                    metadata=json.dumps(metadata) if metadata else None
                )
                
                db.add(transaction)
                await db.flush()
                
                logger.info(f"Deducted {amount} coins from user {user_id} balance (new balance: {new_balance})")
                return transaction
                
        except Exception as e:
            logger.error(f"Error deducting balance for user {user_id}: {e}")
            return None
    
    @staticmethod
    async def has_sufficient_balance(db: AsyncSession, user_id: int, amount: float) -> bool:
        """Check if user has sufficient balance"""
        try:
            current_balance = await BalanceService.get_user_balance(db, user_id)
            return current_balance >= amount
        except Exception as e:
            logger.error(f"Error checking balance for user {user_id}: {e}")
            return False
    
    @staticmethod
    async def create_pending_transaction(
        db: AsyncSession,
        user_id: int,
        amount: float,
        usd_amount: float,
        payment_method: PaymentMethod,
        external_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Transaction]:
        """Create pending transaction for payment processing"""
        try:
            transaction = Transaction(
                user_id=user_id,
                type=TransactionType.DEPOSIT,
                status=TransactionStatus.PENDING,
                amount=amount,
                usd_amount=usd_amount,
                payment_method=payment_method,
                external_id=external_id,
                description=description,
                metadata=json.dumps(metadata) if metadata else None
            )
            
            db.add(transaction)
            await db.commit()
            
            logger.info(f"Created pending transaction for user {user_id}: {amount} coins (${usd_amount})")
            return transaction
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating pending transaction for user {user_id}: {e}")
            return None
    
    @staticmethod
    async def complete_transaction(
        db: AsyncSession,
        transaction_id: int,
        external_id: Optional[str] = None
    ) -> bool:
        """Complete pending transaction and add balance"""
        try:
            # Get transaction
            result = await db.execute(
                select(Transaction).where(Transaction.id == transaction_id)
            )
            transaction = result.scalar_one_or_none()
            
            if not transaction or transaction.status != TransactionStatus.PENDING:
                logger.warning(f"Transaction {transaction_id} not found or not pending")
                return False
            
            # Update external ID if provided
            if external_id:
                transaction.external_id = external_id
            
            # Add balance
            balance_transaction = await BalanceService.add_balance(
                db=db,
                user_id=transaction.user_id,
                amount=transaction.amount,
                transaction_type=transaction.type,
                payment_method=transaction.payment_method,
                external_id=transaction.external_id,
                description=transaction.description,
                usd_amount=transaction.usd_amount,
                metadata=json.loads(transaction.metadata) if transaction.metadata else None
            )
            
            if balance_transaction:
                # Mark original transaction as completed
                transaction.status = TransactionStatus.COMPLETED
                await db.commit()
                
                logger.info(f"Completed transaction {transaction_id} for user {transaction.user_id}")
                return True
            
            return False
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error completing transaction {transaction_id}: {e}")
            return False
    
    @staticmethod
    async def fail_transaction(db: AsyncSession, transaction_id: int, reason: Optional[str] = None) -> bool:
        """Mark transaction as failed"""
        try:
            await db.execute(
                update(Transaction)
                .where(Transaction.id == transaction_id)
                .values(
                    status=TransactionStatus.FAILED,
                    description=reason or "Payment failed"
                )
            )
            await db.commit()
            
            logger.info(f"Marked transaction {transaction_id} as failed: {reason}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error failing transaction {transaction_id}: {e}")
            return False
    
    @staticmethod
    async def get_user_transactions(
        db: AsyncSession,
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> List[Transaction]:
        """Get user transaction history"""
        try:
            result = await db.execute(
                select(Transaction)
                .where(Transaction.user_id == user_id)
                .order_by(desc(Transaction.created_at))
                .limit(limit)
                .offset(offset)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting transactions for user {user_id}: {e}")
            return []
    
    @staticmethod
    async def get_transaction_by_id(
        db: AsyncSession,
        transaction_id: int
    ) -> Optional[Transaction]:
        """Get transaction by ID"""
        try:
            result = await db.execute(
                select(Transaction).where(Transaction.id == transaction_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting transaction by ID {transaction_id}: {e}")
            return None
    
    @staticmethod
    async def get_transaction_by_external_id(
        db: AsyncSession,
        external_id: str,
        payment_method: Optional[PaymentMethod] = None
    ) -> Optional[Transaction]:
        """Get transaction by external payment ID"""
        try:
            query = select(Transaction).where(Transaction.external_id == external_id)
            if payment_method:
                query = query.where(Transaction.payment_method == payment_method)
            
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting transaction by external_id {external_id}: {e}")
            return None
    
    @staticmethod
    async def usd_to_coins(db: AsyncSession, usd_amount: float) -> float:
        """Convert USD to coins using dynamic settings"""
        coins_per_usd = await SettingsService.get_setting(db, "coins_per_usd", 1000)
        return usd_amount * coins_per_usd
    
    @staticmethod
    async def coins_to_usd(db: AsyncSession, coins_amount: float) -> float:
        """Convert coins to USD using dynamic settings"""
        coins_per_usd = await SettingsService.get_setting(db, "coins_per_usd", 1000)
        return coins_amount / coins_per_usd
    
    # Legacy methods for backward compatibility
    @staticmethod
    def usd_to_coins_static(usd_amount: float) -> float:
        """Convert USD to coins using static settings"""
        return usd_amount * settings.coins_per_usd
    
    @staticmethod
    def coins_to_usd_static(coins_amount: float) -> float:
        """Convert coins to USD using static settings"""
        return coins_amount / settings.coins_per_usd
    
    @staticmethod
    async def get_total_deposits(db: AsyncSession) -> float:
        """Get total deposits in USD"""
        try:
            result = await db.execute(
                select(func.sum(Transaction.usd_amount))
                .where(
                    (Transaction.type == TransactionType.DEPOSIT) &
                    (Transaction.status == TransactionStatus.COMPLETED)
                )
            )
            total = result.scalar()
            return total or 0.0
        except Exception as e:
            logger.error(f"Error getting total deposits: {e}")
            return 0.0
    
    @staticmethod
    async def get_transaction_stats(db: AsyncSession, days: int = 30) -> Dict[str, Any]:
        """Get transaction statistics for the last N days"""
        try:
            # This would include more complex queries for analytics
            total_deposits = await BalanceService.get_total_deposits(db)
            
            return {
                "total_deposits_usd": total_deposits,
                "total_deposits_coins": await BalanceService.usd_to_coins(db, total_deposits),
                "period_days": days
            }
        except Exception as e:
            logger.error(f"Error getting transaction stats: {e}")
            return {}

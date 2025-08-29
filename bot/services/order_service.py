"""
Order management service
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, desc, and_
from sqlalchemy.orm import selectinload
from loguru import logger

from bot.database.models import Order, OrderStatus, Service, User, TransactionType
from bot.services.balance_service import BalanceService
from bot.services.service_service import ServiceService
from bot.services.jap_service import jap_service
from bot.services.referral_service import ReferralService


class OrderService:
    """Service for order management"""
    
    @staticmethod
    async def create_order(
        db: AsyncSession,
        user_id: int,
        service_id: int,
        link: str,
        quantity: int
    ) -> Optional[Order]:
        """Create new order"""
        try:
            # Validate service and calculate cost
            service = await ServiceService.get_service_by_id(db, service_id)
            if not service or not service.is_active:
                logger.warning(f"Service {service_id} not found or inactive")
                return None
            
            # Validate quantity
            if not await ServiceService.validate_order_quantity(db, service_id, quantity):
                logger.warning(f"Invalid quantity {quantity} for service {service_id}")
                return None
            
            # Calculate cost
            cost = await ServiceService.calculate_order_cost(db, service_id, quantity)
            if cost <= 0:
                logger.warning(f"Invalid cost {cost} for service {service_id}")
                return None
            
            # Check user balance
            if not await BalanceService.has_sufficient_balance(db, user_id, cost):
                logger.warning(f"Insufficient balance for user {user_id}: required {cost}")
                return None
            
            # Validate link
            if not jap_service.validate_service_link(service.name, link):
                logger.warning(f"Invalid link {link} for service {service.name}")
                return None
            
            # Start transaction
            async with db.begin():
                # Deduct balance
                balance_transaction = await BalanceService.deduct_balance(
                    db=db,
                    user_id=user_id,
                    amount=cost,
                    description=f"Order for {service.name} - {quantity} units",
                    metadata={
                        "service_id": service_id,
                        "service_name": service.name,
                        "quantity": quantity,
                        "link": link
                    }
                )
                
                if not balance_transaction:
                    logger.error(f"Failed to deduct balance for user {user_id}")
                    return None
                
                # Create order
                order = Order(
                    user_id=user_id,
                    service_id=service_id,
                    link=link,
                    quantity=quantity,
                    charge=cost,
                    status=OrderStatus.PENDING
                )
                
                db.add(order)
                await db.flush()  # Get order ID
                
                # Submit order to JAP API
                jap_result = await jap_service.create_order(
                    service_id=service.jap_service_id,
                    link=link,
                    quantity=quantity
                )
                
                if jap_result and "order" in jap_result:
                    order.jap_order_id = int(jap_result["order"])
                    order.status = OrderStatus.IN_PROGRESS
                    logger.info(f"Created order {order.id} with JAP order ID {order.jap_order_id}")
                else:
                    # JAP API failed, but we already deducted balance
                    # Keep order as pending for manual processing
                    logger.error(f"JAP API failed for order {order.id}, keeping as pending")
                
                # Check if this is user's first order (for referral bonus)
                user_orders_count = await OrderService.get_user_orders_count(db, user_id)
                if user_orders_count == 1:  # This is the first order
                    await ReferralService.trigger_referral_activity(db, user_id, "first_order")
                
                return order
                
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return None
    
    @staticmethod
    async def get_order_by_id(db: AsyncSession, order_id: int) -> Optional[Order]:
        """Get order by ID"""
        try:
            result = await db.execute(
                select(Order)
                .options(
                    selectinload(Order.service).selectinload(Service.category),
                    selectinload(Order.user)
                )
                .where(Order.id == order_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return None
    
    @staticmethod
    async def get_user_orders(
        db: AsyncSession,
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> List[Order]:
        """Get user orders with pagination"""
        try:
            result = await db.execute(
                select(Order)
                .options(
                    selectinload(Order.service).selectinload(Service.category)
                )
                .where(Order.user_id == user_id)
                .order_by(desc(Order.created_at))
                .limit(limit)
                .offset(offset)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting orders for user {user_id}: {e}")
            return []
    
    @staticmethod
    async def get_user_orders_count(db: AsyncSession, user_id: int) -> int:
        """Get total orders count for user"""
        try:
            result = await db.execute(
                select(func.count(Order.id)).where(Order.user_id == user_id)
            )
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error getting orders count for user {user_id}: {e}")
            return 0
    
    @staticmethod
    async def update_order_status(
        db: AsyncSession,
        order_id: int,
        status: OrderStatus,
        start_count: Optional[int] = None,
        remains: Optional[int] = None
    ) -> bool:
        """Update order status"""
        try:
            update_data = {"status": status}
            if start_count is not None:
                update_data["start_count"] = start_count
            if remains is not None:
                update_data["remains"] = remains
            
            await db.execute(
                update(Order)
                .where(Order.id == order_id)
                .values(**update_data)
            )
            await db.commit()
            
            logger.info(f"Updated order {order_id} status to {status.value}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating order {order_id} status: {e}")
            return False
    
    @staticmethod
    async def sync_orders_with_jap(db: AsyncSession, limit: int = 100) -> int:
        """Sync order statuses with JAP API"""
        try:
            # Get orders that need status update
            result = await db.execute(
                select(Order)
                .where(
                    and_(
                        Order.jap_order_id.isnot(None),
                        Order.status.in_([OrderStatus.PENDING, OrderStatus.IN_PROGRESS])
                    )
                )
                .limit(limit)
            )
            orders = result.scalars().all()
            
            if not orders:
                return 0
            
            logger.info(f"Syncing {len(orders)} orders with JAP API")
            
            # Get order IDs for batch status check
            jap_order_ids = [order.jap_order_id for order in orders if order.jap_order_id]
            
            if not jap_order_ids:
                return 0
            
            # Get statuses from JAP API
            jap_statuses = await jap_service.get_multiple_orders_status(jap_order_ids)
            
            if not jap_statuses:
                logger.warning("Failed to get order statuses from JAP API")
                return 0
            
            updated_count = 0
            
            # Update order statuses
            for order in orders:
                if order.jap_order_id and str(order.jap_order_id) in jap_statuses:
                    jap_status_data = jap_statuses[str(order.jap_order_id)]
                    
                    # Map JAP status to local status
                    jap_status = jap_status_data.get("status", "")
                    local_status = jap_service.map_jap_status_to_local(jap_status)
                    
                    # Get additional data
                    start_count = jap_status_data.get("start_count")
                    remains = jap_status_data.get("remains")
                    
                    # Update if status changed
                    if order.status.value != local_status:
                        success = await OrderService.update_order_status(
                            db=db,
                            order_id=order.id,
                            status=OrderStatus(local_status),
                            start_count=int(start_count) if start_count else None,
                            remains=int(remains) if remains else None
                        )
                        if success:
                            updated_count += 1
            
            logger.info(f"Updated {updated_count} order statuses from JAP API")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error syncing orders with JAP API: {e}")
            return 0
    
    @staticmethod
    async def get_orders_stats(db: AsyncSession) -> Dict[str, Any]:
        """Get orders statistics"""
        try:
            # Total orders
            total_result = await db.execute(select(func.count(Order.id)))
            total_orders = total_result.scalar() or 0
            
            # Orders by status
            status_results = await db.execute(
                select(Order.status, func.count(Order.id))
                .group_by(Order.status)
            )
            
            status_counts = {}
            for status, count in status_results:
                status_counts[status.value] = count
            
            # Total revenue
            revenue_result = await db.execute(
                select(func.sum(Order.charge))
                .where(Order.status.in_([OrderStatus.COMPLETED, OrderStatus.PARTIAL]))
            )
            total_revenue = revenue_result.scalar() or 0.0
            
            return {
                "total_orders": total_orders,
                "status_counts": status_counts,
                "total_revenue_coins": total_revenue,
                "total_revenue_usd": BalanceService.coins_to_usd(total_revenue)
            }
            
        except Exception as e:
            logger.error(f"Error getting orders stats: {e}")
            return {}
    
    @staticmethod
    async def get_recent_orders(
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0
    ) -> List[Order]:
        """Get recent orders for admin"""
        try:
            result = await db.execute(
                select(Order)
                .options(
                    selectinload(Order.service).selectinload(Service.category),
                    selectinload(Order.user)
                )
                .order_by(desc(Order.created_at))
                .limit(limit)
                .offset(offset)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting recent orders: {e}")
            return []
    
    @staticmethod
    async def cancel_order(db: AsyncSession, order_id: int, refund: bool = True) -> bool:
        """Cancel order and optionally refund"""
        try:
            order = await OrderService.get_order_by_id(db, order_id)
            if not order:
                return False
            
            if order.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
                logger.warning(f"Cannot cancel order {order_id} with status {order.status.value}")
                return False
            
            # Start transaction
            async with db.begin():
                # Update order status
                order.status = OrderStatus.CANCELLED
                
                # Refund if requested and order was charged
                if refund and order.charge > 0:
                    refund_transaction = await BalanceService.add_balance(
                        db=db,
                        user_id=order.user_id,
                        amount=order.charge,
                        transaction_type=TransactionType.REFUND,
                        description=f"Refund for cancelled order #{order_id}",
                        metadata={
                            "order_id": order_id,
                            "original_charge": order.charge
                        }
                    )
                    
                    if not refund_transaction:
                        logger.error(f"Failed to refund order {order_id}")
                        return False
                
                logger.info(f"Cancelled order {order_id} with{'out' if not refund else ''} refund")
                return True
                
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False

"""
Service management for SMM services - Updated for JAP API compatibility
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_
from sqlalchemy.orm import selectinload
from loguru import logger
from datetime import datetime

from bot.database.models import ServiceCategory, Service, JAPBalance
from bot.services.jap_service import jap_service
from bot.config import settings


class ServiceService:
    """Service for managing SMM services"""
    
    @staticmethod
    async def get_services_from_jap() -> List[Dict[str, Any]]:
        """Get services directly from JAP API without syncing to database"""
        try:
            logger.info("Fetching services from JAP API...")
            services = await jap_service.get_services()
            
            if not services:
                logger.warning("No services received from JAP API")
                return []
            
            logger.info(f"Successfully fetched {len(services)} services from JAP API")
            return services
            
        except Exception as e:
            logger.error(f"Error fetching services from JAP API: {e}")
            return []
    
    @staticmethod
    async def get_service_from_jap(service_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific service from JAP API"""
        try:
            services = await ServiceService.get_services_from_jap()
            
            for service in services:
                if int(service.get("service", 0)) == service_id:
                    return service
            
            logger.warning(f"Service {service_id} not found in JAP API")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching service {service_id} from JAP API: {e}")
            return None
    
    @staticmethod
    async def create_order_via_jap(service_id: int, link: str, quantity: int) -> Optional[Dict[str, Any]]:
        """Create order directly via JAP API"""
        try:
            logger.info(f"Creating order via JAP API: service={service_id}, link={link}, quantity={quantity}")
            
            order_result = await jap_service.create_order(
                service_id=service_id,
                link=link,
                quantity=quantity
            )
            
            if order_result and "order" in order_result:
                logger.info(f"Order created successfully via JAP API: {order_result['order']}")
                return order_result
            else:
                logger.error(f"Failed to create order via JAP API: {order_result}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating order via JAP API: {e}")
            return None
    
    @staticmethod
    async def get_order_status_via_jap(order_id: int) -> Optional[Dict[str, Any]]:
        """Get order status directly via JAP API"""
        try:
            logger.info(f"Getting order status via JAP API: order_id={order_id}")
            
            status_result = await jap_service.get_order_status(order_id)
            
            if status_result:
                logger.info(f"Order status retrieved via JAP API: {status_result}")
                return status_result
            else:
                logger.error(f"Failed to get order status via JAP API for order {order_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting order status via JAP API: {e}")
            return None
    
    @staticmethod
    async def get_jap_balance() -> Optional[Dict[str, Any]]:
        """Get JAP balance directly from API"""
        try:
            logger.info("Getting JAP balance...")
            
            balance_result = await jap_service.get_balance()
            
            if balance_result and "balance" in balance_result:
                logger.info(f"JAP balance: {balance_result['balance']} {balance_result.get('currency', 'USD')}")
                return balance_result
            else:
                logger.error(f"Failed to get JAP balance: {balance_result}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting JAP balance: {e}")
            return None

    @staticmethod
    async def sync_services_from_jap(db: AsyncSession) -> bool:
        """Synchronize services from JAP API with improved error handling"""
        try:
            # Get services from JAP API
            jap_services = await jap_service.get_services()
            if not jap_services:
                logger.error("Failed to get services from JAP API")
                return False
            
            logger.info(f"Syncing {len(jap_services)} services from JAP API")
            
            # Group services by category
            categories_map = {}
            for jap_service_data in jap_services:
                category_name = jap_service_data.get("category", "Other")
                if category_name not in categories_map:
                    categories_map[category_name] = []
                categories_map[category_name].append(jap_service_data)
            
            # Create or update categories and services
            for category_name, services_data in categories_map.items():
                # Get or create category
                category = await ServiceService._get_or_create_category(db, category_name)
                if not category:
                    continue
                
                # Create or update services
                for service_data in services_data:
                    await ServiceService._sync_service(db, category.id, service_data)
            
            await db.commit()
            logger.info("Successfully synced services from JAP API")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error syncing services from JAP API: {e}")
            return False
    
    @staticmethod
    async def _get_or_create_category(db: AsyncSession, name: str) -> Optional[ServiceCategory]:
        """Get or create service category"""
        try:
            # Check if category exists
            result = await db.execute(
                select(ServiceCategory).where(ServiceCategory.name == name)
            )
            category = result.scalar_one_or_none()
            
            if not category:
                # Create new category
                category = ServiceCategory(
                    name=name,
                    description=f"Services for {name}",
                    is_active=True,
                    sort_order=0
                )
                db.add(category)
                await db.flush()
                logger.info(f"Created new service category: {name}")
            
            return category
            
        except Exception as e:
            logger.error(f"Error getting/creating category {name}: {e}")
            return None
    
    @staticmethod
    async def _sync_service(db: AsyncSession, category_id: int, jap_service_data: Dict[str, Any]) -> bool:
        """Sync individual service from JAP API with improved data handling"""
        try:
            jap_service_id = int(jap_service_data.get("service", 0))
            if not jap_service_id:
                return False
            
            # Check if service exists
            result = await db.execute(
                select(Service).where(Service.jap_service_id == jap_service_id)
            )
            service = result.scalar_one_or_none()
            
            # Calculate price in coins
            rate_usd = float(jap_service_data.get("rate", 0))
            price_coins = rate_usd * settings.coins_per_usd if rate_usd > 0 else 0
            
            # Prepare metadata
            meta_data = {
                "jap_data": jap_service_data,
                "last_sync": str(datetime.now())
            }
            
            if service:
                # Update existing service
                service.name = jap_service_data.get("name", "")
                service.description = jap_service_data.get("description", "")
                service.service_type = jap_service_data.get("type", "")
                service.price_per_1000 = price_coins
                service.jap_rate_usd = rate_usd
                service.min_quantity = int(jap_service_data.get("min", 100))
                service.max_quantity = int(jap_service_data.get("max", 100000))
                service.category_id = category_id
                service.supports_refill = bool(jap_service_data.get("refill", False))
                service.supports_cancel = bool(jap_service_data.get("cancel", False))
                service.supports_dripfeed = bool(jap_service_data.get("dripfeed", False))
                service.meta_data = meta_data
                service.is_active = True
            else:
                # Create new service
                service = Service(
                    category_id=category_id,
                    jap_service_id=jap_service_id,
                    name=jap_service_data.get("name", ""),
                    description=jap_service_data.get("description", ""),
                    service_type=jap_service_data.get("type", ""),
                    price_per_1000=price_coins,
                    jap_rate_usd=rate_usd,
                    min_quantity=int(jap_service_data.get("min", 100)),
                    max_quantity=int(jap_service_data.get("max", 100000)),
                    supports_refill=bool(jap_service_data.get("refill", False)),
                    supports_cancel=bool(jap_service_data.get("cancel", False)),
                    supports_dripfeed=bool(jap_service_data.get("dripfeed", False)),
                    meta_data=meta_data,
                    is_active=True,
                    sort_order=0
                )
                db.add(service)
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing service {jap_service_data}: {e}")
            return False
    
    @staticmethod
    async def update_jap_balance(db: AsyncSession) -> bool:
        """Update JAP balance in database"""
        try:
            balance_info = await ServiceService.get_jap_balance()
            if not balance_info:
                return False
            
            balance = float(balance_info.get("balance", 0))
            currency = balance_info.get("currency", "USD")
            
            # Check if balance record exists
            result = await db.execute(select(JAPBalance))
            jap_balance = result.scalar_one_or_none()
            
            if jap_balance:
                # Update existing balance
                jap_balance.balance = balance
                jap_balance.currency = currency
            else:
                # Create new balance record
                jap_balance = JAPBalance(
                    balance=balance,
                    currency=currency
                )
                db.add(jap_balance)
            
            await db.commit()
            logger.info(f"JAP balance updated: {balance} {currency}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating JAP balance: {e}")
            return False

    @staticmethod
    async def get_active_categories(db: AsyncSession) -> List[ServiceCategory]:
        """Get all active service categories"""
        try:
            result = await db.execute(
                select(ServiceCategory)
                .where(ServiceCategory.is_active == True)
                .order_by(ServiceCategory.sort_order, ServiceCategory.name)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting active categories: {e}")
            return []
    
    @staticmethod
    async def get_services_by_category(db: AsyncSession, category_id: int) -> List[Service]:
        """Get all active services in a category"""
        try:
            result = await db.execute(
                select(Service)
                .where(
                    and_(
                        Service.category_id == category_id,
                        Service.is_active == True
                    )
                )
                .order_by(Service.sort_order, Service.name)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting services for category {category_id}: {e}")
            return []
    
    @staticmethod
    async def get_service_by_id(db: AsyncSession, service_id: int) -> Optional[Service]:
        """Get service by ID"""
        try:
            result = await db.execute(
                select(Service)
                .options(selectinload(Service.category))
                .where(Service.id == service_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting service {service_id}: {e}")
            return None
    
    @staticmethod
    async def get_service_by_jap_id(db: AsyncSession, jap_service_id: int) -> Optional[Service]:
        """Get service by JAP service ID"""
        try:
            result = await db.execute(
                select(Service)
                .options(selectinload(Service.category))
                .where(Service.jap_service_id == jap_service_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting service by JAP ID {jap_service_id}: {e}")
            return None
    
    @staticmethod
    async def calculate_order_cost(db: AsyncSession, service_id: int, quantity: int) -> float:
        """Calculate order cost in coins"""
        try:
            service = await ServiceService.get_service_by_id(db, service_id)
            if not service:
                return 0.0
            
            # Calculate cost: (price_per_1000 * quantity) / 1000
            cost = (service.price_per_1000 * quantity) / 1000
            return round(cost, 2)
            
        except Exception as e:
            logger.error(f"Error calculating order cost for service {service_id}: {e}")
            return 0.0
    
    @staticmethod
    async def validate_order_quantity(db: AsyncSession, service_id: int, quantity: int) -> bool:
        """Validate order quantity against service limits"""
        try:
            service = await ServiceService.get_service_by_id(db, service_id)
            if not service:
                return False
            
            return service.min_quantity <= quantity <= service.max_quantity
            
        except Exception as e:
            logger.error(f"Error validating order quantity for service {service_id}: {e}")
            return False
    
    @staticmethod
    async def get_popular_services(db: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular services by order count"""
        try:
            # This would require joining with orders table
            # For now, return top services by name (placeholder)
            result = await db.execute(
                select(Service, ServiceCategory.name.label('category_name'))
                .join(ServiceCategory)
                .where(Service.is_active == True)
                .order_by(Service.name)
                .limit(limit)
            )
            
            popular_services = []
            for service, category_name in result:
                popular_services.append({
                    "id": service.id,
                    "name": service.name,
                    "category": category_name,
                    "price_per_1000": service.price_per_1000,
                    "orders_count": 0  # Placeholder
                })
            
            return popular_services
            
        except Exception as e:
            logger.error(f"Error getting popular services: {e}")
            return []
    
    @staticmethod
    async def update_service_status(db: AsyncSession, service_id: int, is_active: bool) -> bool:
        """Update service active status"""
        try:
            await db.execute(
                update(Service)
                .where(Service.id == service_id)
                .values(is_active=is_active)
            )
            await db.commit()
            
            logger.info(f"Updated service {service_id} status to {'active' if is_active else 'inactive'}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating service {service_id} status: {e}")
            return False
    
    @staticmethod
    async def update_service_price(db: AsyncSession, service_id: int, price_per_1000: float) -> bool:
        """Update service price"""
        try:
            await db.execute(
                update(Service)
                .where(Service.id == service_id)
                .values(price_per_1000=price_per_1000)
            )
            await db.commit()
            
            logger.info(f"Updated service {service_id} price to {price_per_1000} coins per 1000")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating service {service_id} price: {e}")
            return False
    
    @staticmethod
    async def create_demo_categories_and_services(db: AsyncSession) -> bool:
        """Create demo categories and services when none are available"""
        try:
            logger.info("Creating demo categories and services")
            
            # Check if categories already exist to avoid duplicates
            existing_count = await db.execute(
                select(func.count(ServiceCategory.id))
            )
            if existing_count.scalar() > 0:
                logger.info("Demo categories already exist, skipping creation")
                return True
            
            # Create demo categories
            categories = {
                "Instagram": "Instagram followers, likes, comments, and views",
                "TikTok": "TikTok followers, likes, comments, and views",
                "YouTube": "YouTube subscribers, views, likes, and comments",
                "Twitter": "Twitter followers, likes, retweets, and views",
                "Facebook": "Facebook page likes, followers, and post engagements",
                "Telegram": "Telegram channel members and post views"
            }
            
            created_categories = {}
            
            # Create categories with proper transaction handling
            for name, description in categories.items():
                try:
                    category = ServiceCategory(
                        name=name,
                        description=description,
                        is_active=True,
                        sort_order=list(categories.keys()).index(name)
                    )
                    db.add(category)
                    await db.flush()  # Flush to get ID
                    created_categories[name] = category.id
                    logger.info(f"Created demo category: {name} (ID: {category.id})")
                except Exception as e:
                    logger.warning(f"Failed to create category {name}: {e}")
                    await db.rollback()
                    return False
            
            # Create demo services with pricing according to requirements
            services_data = [
                # Telegram - 15,000 coins per 1K members
                {"category": "Telegram", "name": "Telegram Channel Members | Premium | HQ", "price": 15000, "min": 100, "max": 50000},
                {"category": "Telegram", "name": "Telegram Group Members | Real | Active", "price": 15000, "min": 100, "max": 30000},
                {"category": "Telegram", "name": "Telegram Post Views | Fast | Instant", "price": 5000, "min": 100, "max": 100000},
                
                # YouTube - 8,000 coins per 1K views
                {"category": "YouTube", "name": "YouTube Views | HQ | Max 1M", "price": 8000, "min": 1000, "max": 1000000},
                {"category": "YouTube", "name": "YouTube Subscribers | Real | Stable", "price": 20000, "min": 100, "max": 10000},
                {"category": "YouTube", "name": "YouTube Likes | Fast | Non-drop", "price": 10000, "min": 50, "max": 50000},
                
                # TikTok - 5,000 coins per 1K views
                {"category": "TikTok", "name": "TikTok Views | Max 1M | Instant", "price": 5000, "min": 1000, "max": 1000000},
                {"category": "TikTok", "name": "TikTok Followers | Max 50K | HQ", "price": 12000, "min": 100, "max": 50000},
                {"category": "TikTok", "name": "TikTok Likes | Max 100K | Fast", "price": 8000, "min": 100, "max": 100000},
                
                # Instagram - 12,000 coins per 1K likes
                {"category": "Instagram", "name": "Instagram Likes | Premium | Instant", "price": 12000, "min": 50, "max": 50000},
                {"category": "Instagram", "name": "Instagram Followers | Real | Active", "price": 15000, "min": 100, "max": 10000},
                {"category": "Instagram", "name": "Instagram Comments | Custom | Max 1K", "price": 20000, "min": 10, "max": 1000},
                
                # Twitter
                {"category": "Twitter", "name": "Twitter Followers | Max 50K | HQ", "price": 12000, "min": 100, "max": 50000},
                {"category": "Twitter", "name": "Twitter Likes | Max 100K | Fast", "price": 8000, "min": 50, "max": 100000},
                {"category": "Twitter", "name": "Twitter Retweets | Max 10K | Real", "price": 10000, "min": 50, "max": 10000},
                
                # Facebook
                {"category": "Facebook", "name": "Facebook Page Likes | Max 100K | HQ", "price": 10000, "min": 100, "max": 100000},
                {"category": "Facebook", "name": "Facebook Post Likes | Max 50K | Fast", "price": 8000, "min": 50, "max": 50000},
                {"category": "Facebook", "name": "Facebook Followers | Max 50K | Real", "price": 12000, "min": 100, "max": 50000}
            ]
            
            # Create services with proper error handling
            services_created = 0
            for i, service_data in enumerate(services_data):
                try:
                    category_id = created_categories.get(service_data["category"])
                    if category_id:
                        service = Service(
                            category_id=category_id,
                            jap_service_id=10000 + i,  # Create fake JAP service IDs starting from 10000
                            name=service_data["name"],
                            description=f"High-quality {service_data['name'].split('|')[0].strip()} service",
                            price_per_1000=service_data["price"],
                            min_quantity=service_data["min"],
                            max_quantity=service_data["max"],
                            is_active=True,
                            sort_order=i % 10  # Sort within category
                        )
                        db.add(service)
                        services_created += 1
                        logger.info(f"Created demo service: {service_data['name']}")
                except Exception as e:
                    logger.warning(f"Failed to create service {service_data['name']}: {e}")
                    continue
            
            # Commit all changes at once
            await db.commit()
            logger.info(f"Demo categories and services created successfully ({services_created} services)")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating demo categories and services: {e}")
            return False
    
    @staticmethod
    async def get_services_by_platform_and_type(db: AsyncSession, platform: str, service_type: str) -> List[Service]:
        """Get services by platform and service type"""
        try:
            # Create search terms based on platform and service type
            search_terms = f"{platform} {service_type}".replace("_", " ")
            
            result = await db.execute(
                select(Service)
                .where(
                    and_(
                        Service.is_active == True,
                        Service.name.ilike(f"%{search_terms}%")
                    )
                )
                .options(selectinload(Service.category))
                .order_by(Service.sort_order, Service.name)
                .limit(20)
            )
            
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting services by platform and type: {e}")
            return []
    
    @staticmethod
    async def get_services_by_type(db: AsyncSession, service_type: str) -> List[Service]:
        """Get services by service type"""
        try:
            # Clean up service type for search
            search_term = service_type.replace("_", " ")
            
            result = await db.execute(
                select(Service)
                .where(
                    and_(
                        Service.is_active == True,
                        Service.name.ilike(f"%{search_term}%")
                    )
                )
                .options(selectinload(Service.category))
                .order_by(Service.sort_order, Service.name)
                .limit(20)
            )
            
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting services by type: {e}")
            return []
    
    @staticmethod
    async def get_popular_services(db: AsyncSession, limit: int = 10) -> List[Service]:
        """Get popular services (by order count or predefined popularity)"""
        try:
            # For now, return services with lowest sort_order as "popular"
            # In future, this could be based on actual order statistics
            result = await db.execute(
                select(Service)
                .where(Service.is_active == True)
                .options(selectinload(Service.category))
                .order_by(Service.sort_order, Service.price_per_1000)
                .limit(limit)
            )
            
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting popular services: {e}")
            return []
    
    @staticmethod
    async def get_services_stats(db: AsyncSession) -> Dict[str, Any]:
        """Get services statistics"""
        try:
            # Total services
            total_result = await db.execute(select(func.count(Service.id)))
            total_services = total_result.scalar() or 0
            
            # Active services
            active_result = await db.execute(
                select(func.count(Service.id)).where(Service.is_active == True)
            )
            active_services = active_result.scalar() or 0
            
            # Categories count
            categories_result = await db.execute(select(func.count(ServiceCategory.id)))
            total_categories = categories_result.scalar() or 0
            
            return {
                "total_services": total_services,
                "active_services": active_services,
                "inactive_services": total_services - active_services,
                "total_categories": total_categories
            }
            
        except Exception as e:
            logger.error(f"Error getting services stats: {e}")
            return {
                "total_services": 0,
                "active_services": 0,
                "inactive_services": 0,
                "total_categories": 0
            }

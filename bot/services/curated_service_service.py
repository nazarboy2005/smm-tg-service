"""
Service for managing admin-curated services
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload
from loguru import logger
from datetime import datetime

from bot.database.models import AdminCuratedService
from bot.services.jap_service import jap_service


class CuratedServiceService:
    """Service for managing admin-curated services"""
    
    @staticmethod
    async def add_service(
        db: AsyncSession,
        jap_service_id: int,
        custom_name: str,
        custom_description: str,
        custom_price_per_1000: float,
        admin_id: int
    ) -> Optional[AdminCuratedService]:
        """Add a new curated service"""
        try:
            # Check if service already exists
            existing = await db.execute(
                select(AdminCuratedService).where(
                    AdminCuratedService.jap_service_id == jap_service_id
                )
            )
            if existing.scalar_one_or_none():
                logger.warning(f"Service {jap_service_id} already exists in curated services")
                return None
            
            # Get service details from JAP to extract platform and service type
            jap_services = await jap_service.get_services()
            jap_service_data = None
            
            for service in jap_services:
                if service.get("service") == jap_service_id:
                    jap_service_data = service
                    break
            
            if not jap_service_data:
                logger.error(f"JAP service {jap_service_id} not found")
                return None
            
            # Extract platform and service type from JAP service
            service_name = jap_service_data.get("name", "").lower()
            platform = CuratedServiceService._extract_platform(service_name)
            service_type = CuratedServiceService._extract_service_type(service_name)
            
            # Create curated service
            curated_service = AdminCuratedService(
                jap_service_id=jap_service_id,
                custom_name=custom_name,
                custom_description=custom_description,
                custom_price_per_1000=custom_price_per_1000,
                platform=platform,
                service_type=service_type,
                added_by_admin_id=admin_id
            )
            
            db.add(curated_service)
            await db.commit()
            await db.refresh(curated_service)
            
            logger.info(f"Added curated service: {custom_name} (JAP ID: {jap_service_id})")
            return curated_service
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error adding curated service: {e}")
            return None
    
    @staticmethod
    async def get_all_curated_services(db: AsyncSession, active_only: bool = True) -> List[AdminCuratedService]:
        """Get all curated services"""
        try:
            query = select(AdminCuratedService)
            
            if active_only:
                query = query.where(AdminCuratedService.is_active == True)
            
            query = query.order_by(AdminCuratedService.sort_order, AdminCuratedService.custom_name)
            
            result = await db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting curated services: {e}")
            return []
    
    @staticmethod
    async def get_curated_service_by_id(db: AsyncSession, service_id: int) -> Optional[AdminCuratedService]:
        """Get curated service by ID"""
        try:
            result = await db.execute(
                select(AdminCuratedService).where(AdminCuratedService.id == service_id)
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting curated service {service_id}: {e}")
            return None
    
    @staticmethod
    async def get_curated_service_by_jap_id(db: AsyncSession, jap_service_id: int) -> Optional[AdminCuratedService]:
        """Get curated service by JAP service ID"""
        try:
            result = await db.execute(
                select(AdminCuratedService).where(AdminCuratedService.jap_service_id == jap_service_id)
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting curated service by JAP ID {jap_service_id}: {e}")
            return None
    
    @staticmethod
    async def update_service(
        db: AsyncSession,
        service_id: int,
        custom_name: Optional[str] = None,
        custom_description: Optional[str] = None,
        custom_price_per_1000: Optional[float] = None,
        is_active: Optional[bool] = None
    ) -> bool:
        """Update curated service"""
        try:
            # Get existing service
            result = await db.execute(
                select(AdminCuratedService).where(AdminCuratedService.id == service_id)
            )
            service = result.scalar_one_or_none()
            
            if not service:
                logger.error(f"Curated service {service_id} not found")
                return False
            
            # Update fields
            if custom_name is not None:
                service.custom_name = custom_name
            if custom_description is not None:
                service.custom_description = custom_description
            if custom_price_per_1000 is not None:
                service.custom_price_per_1000 = custom_price_per_1000
            if is_active is not None:
                service.is_active = is_active
            
            service.updated_at = datetime.utcnow()
            
            await db.commit()
            logger.info(f"Updated curated service {service_id}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating curated service {service_id}: {e}")
            return False
    
    @staticmethod
    async def delete_service(db: AsyncSession, service_id: int) -> bool:
        """Delete curated service"""
        try:
            result = await db.execute(
                delete(AdminCuratedService).where(AdminCuratedService.id == service_id)
            )
            
            if result.rowcount == 0:
                logger.error(f"Curated service {service_id} not found")
                return False
            
            await db.commit()
            logger.info(f"Deleted curated service {service_id}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting curated service {service_id}: {e}")
            return False
    
    @staticmethod
    async def get_services_by_platform(db: AsyncSession, platform: str) -> List[AdminCuratedService]:
        """Get curated services by platform"""
        try:
            result = await db.execute(
                select(AdminCuratedService)
                .where(
                    and_(
                        AdminCuratedService.platform == platform,
                        AdminCuratedService.is_active == True
                    )
                )
                .order_by(AdminCuratedService.sort_order, AdminCuratedService.custom_name)
            )
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting curated services for platform {platform}: {e}")
            return []
    
    @staticmethod
    def _extract_platform(service_name: str) -> str:
        """Extract platform from service name"""
        service_name = service_name.lower()
        
        if any(word in service_name for word in ['instagram', 'ig']):
            return 'instagram'
        elif any(word in service_name for word in ['youtube', 'yt']):
            return 'youtube'
        elif any(word in service_name for word in ['tiktok', 'tt']):
            return 'tiktok'
        elif any(word in service_name for word in ['twitter', 'tw']):
            return 'twitter'
        elif any(word in service_name for word in ['telegram', 'tg']):
            return 'telegram'
        elif any(word in service_name for word in ['facebook', 'fb']):
            return 'facebook'
        elif any(word in service_name for word in ['linkedin', 'li']):
            return 'linkedin'
        else:
            return 'other'
    
    @staticmethod
    def _extract_service_type(service_name: str) -> str:
        """Extract service type from service name"""
        service_name = service_name.lower()
        
        if any(word in service_name for word in ['follower', 'followers', 'subscriber', 'subscribers']):
            return 'followers'
        elif any(word in service_name for word in ['like', 'likes']):
            return 'likes'
        elif any(word in service_name for word in ['view', 'views', 'watch', 'watches']):
            return 'views'
        elif any(word in service_name for word in ['comment', 'comments']):
            return 'comments'
        elif any(word in service_name for word in ['share', 'shares', 'retweet', 'retweets']):
            return 'shares'
        elif any(word in service_name for word in ['reaction', 'reactions']):
            return 'reactions'
        else:
            return 'other'

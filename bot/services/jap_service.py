"""
JAP API integration service for SMM services
"""
import aiohttp
import asyncio
from typing import Optional, List, Dict, Any
from loguru import logger

from bot.config import settings


class JAPService:
    """Service for JAP API integration"""
    
    def __init__(self):
        self.api_url = "https://justanotherpanel.com/api/v2"
        self.api_key = settings.jap_api_key
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _make_request(
        self,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request to JAP API"""
        try:
            session = await self._get_session()
            
            # Add API key to data
            data["key"] = self.api_key
            
            async with session.post(self.api_url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    logger.error(f"JAP API request failed: {response.status} - {await response.text()}")
                    return None
                    
        except Exception as e:
            logger.error(f"JAP API request error: {e}")
            return None
    
    async def get_services(self) -> Optional[List[Dict[str, Any]]]:
        """Get available services from JAP API"""
        try:
            data = {"action": "services"}
            result = await self._make_request(data)
            if result and isinstance(result, list):
                logger.info(f"Retrieved {len(result)} services from JAP API")
                return result
            return None
        except Exception as e:
            logger.error(f"Error getting services from JAP API: {e}")
            return None
    
    async def get_service_by_id(self, service_id: int) -> Optional[Dict[str, Any]]:
        """Get specific service by ID"""
        try:
            services = await self.get_services()
            if services:
                for service in services:
                    if service.get("service") == service_id:
                        return service
            return None
        except Exception as e:
            logger.error(f"Error getting service {service_id} from JAP API: {e}")
            return None
    
    async def create_order(
        self,
        service_id: int,
        link: str,
        quantity: int,
        runs: Optional[int] = None,
        interval: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Create order via JAP API"""
        try:
            data = {
                "action": "add",
                "service": service_id,
                "link": link,
                "quantity": quantity
            }
            
            # Add optional parameters
            if runs is not None:
                data["runs"] = runs
            if interval is not None:
                data["interval"] = interval
            
            result = await self._make_request(data)
            if result and "order" in result:
                logger.info(f"Created JAP order: service {service_id}, quantity {quantity}, order_id {result.get('order')}")
                return result
            return None
            
        except Exception as e:
            logger.error(f"Error creating JAP order: {e}")
            return None
    
    async def get_order_status(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get order status from JAP API"""
        try:
            data = {
                "action": "status",
                "order": order_id
            }
            
            result = await self._make_request(data)
            if result:
                return result
            return None
            
        except Exception as e:
            logger.error(f"Error getting JAP order status {order_id}: {e}")
            return None
    
    async def get_multiple_orders_status(self, order_ids: List[int]) -> Optional[Dict[str, Any]]:
        """Get status of multiple orders"""
        try:
            data = {
                "action": "status",
                "orders": ",".join(map(str, order_ids))
            }
            
            result = await self._make_request(data)
            if result:
                return result
            return None
            
        except Exception as e:
            logger.error(f"Error getting multiple JAP orders status: {e}")
            return None
    
    async def create_refill(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Create refill for an order"""
        try:
            data = {
                "action": "refill",
                "order": order_id
            }
            
            result = await self._make_request(data)
            if result and "refill" in result:
                logger.info(f"Created refill for order {order_id}: refill_id {result.get('refill')}")
                return result
            return None
            
        except Exception as e:
            logger.error(f"Error creating refill for order {order_id}: {e}")
            return None
    
    async def create_multiple_refills(self, order_ids: List[int]) -> Optional[List[Dict[str, Any]]]:
        """Create refills for multiple orders"""
        try:
            data = {
                "action": "refill",
                "orders": ",".join(map(str, order_ids))
            }
            
            result = await self._make_request(data)
            if result and isinstance(result, list):
                logger.info(f"Created refills for {len(result)} orders")
                return result
            return None
            
        except Exception as e:
            logger.error(f"Error creating multiple refills: {e}")
            return None
    
    async def get_refill_status(self, refill_id: int) -> Optional[Dict[str, Any]]:
        """Get refill status"""
        try:
            data = {
                "action": "refill_status",
                "refill": refill_id
            }
            
            result = await self._make_request(data)
            if result:
                return result
            return None
            
        except Exception as e:
            logger.error(f"Error getting refill status {refill_id}: {e}")
            return None
    
    async def get_multiple_refills_status(self, refill_ids: List[int]) -> Optional[List[Dict[str, Any]]]:
        """Get status of multiple refills"""
        try:
            data = {
                "action": "refill_status",
                "refills": ",".join(map(str, refill_ids))
            }
            
            result = await self._make_request(data)
            if result and isinstance(result, list):
                return result
            return None
            
        except Exception as e:
            logger.error(f"Error getting multiple refills status: {e}")
            return None
    
    async def cancel_orders(self, order_ids: List[int]) -> Optional[List[Dict[str, Any]]]:
        """Cancel multiple orders"""
        try:
            data = {
                "action": "cancel",
                "orders": ",".join(map(str, order_ids))
            }
            
            result = await self._make_request(data)
            if result and isinstance(result, list):
                logger.info(f"Cancelled {len(result)} orders")
                return result
            return None
            
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
            return None
    
    async def get_balance(self) -> Optional[float]:
        """Get JAP API balance"""
        try:
            data = {"action": "balance"}
            result = await self._make_request(data)
            
            if result and "balance" in result:
                balance = float(result["balance"])
                logger.info(f"JAP API balance: ${balance}")
                return balance
            return None
            
        except Exception as e:
            logger.error(f"Error getting JAP balance: {e}")
            return None
    
    def map_jap_status_to_local(self, jap_status: str) -> str:
        """Map JAP API status to local order status"""
        status_mapping = {
            "Pending": "pending",
            "In progress": "in_progress",
            "Processing": "in_progress",
            "Completed": "completed",
            "Partial": "partial",
            "Canceled": "cancelled",
            "Error": "error"
        }
        return status_mapping.get(jap_status, "pending")
    
    def calculate_service_price(self, jap_service: Dict[str, Any], quantity: int) -> float:
        """Calculate price for service and quantity in coins"""
        try:
            # JAP API returns rate per 1000
            rate_per_1000 = float(jap_service.get("rate", 0))
            
            # Convert to our coin system
            # Assuming JAP rate is in USD, convert to coins
            price_usd = (rate_per_1000 * quantity) / 1000
            price_coins = price_usd * settings.coins_per_usd
            
            return round(price_coins, 2)
            
        except Exception as e:
            logger.error(f"Error calculating service price: {e}")
            return 0.0
    
    def validate_service_link(self, service_type: str, link: str) -> bool:
        """Validate social media link based on service type"""
        try:
            link = link.lower().strip()
            
            # Basic URL validation
            if not link.startswith(('http://', 'https://')):
                return False
            
            # Service-specific validation
            if 'instagram' in service_type.lower():
                return 'instagram.com' in link
            elif 'facebook' in service_type.lower():
                return 'facebook.com' in link or 'fb.com' in link
            elif 'twitter' in service_type.lower() or 'x.com' in service_type.lower():
                return 'twitter.com' in link or 'x.com' in link
            elif 'youtube' in service_type.lower():
                return 'youtube.com' in link or 'youtu.be' in link
            elif 'tiktok' in service_type.lower():
                return 'tiktok.com' in link
            elif 'telegram' in service_type.lower():
                return 't.me' in link or 'telegram.me' in link
            
            # If no specific validation, accept any valid URL
            return True
            
        except Exception as e:
            logger.error(f"Error validating service link: {e}")
            return False
    
    def get_service_category(self, service_name: str) -> str:
        """Determine service category from service name"""
        service_name = service_name.lower()
        
        if 'instagram' in service_name:
            return 'Instagram'
        elif 'facebook' in service_name:
            return 'Facebook'
        elif 'twitter' in service_name or 'x.com' in service_name:
            return 'Twitter/X'
        elif 'youtube' in service_name:
            return 'YouTube'
        elif 'tiktok' in service_name:
            return 'TikTok'
        elif 'telegram' in service_name:
            return 'Telegram'
        elif 'linkedin' in service_name:
            return 'LinkedIn'
        elif 'spotify' in service_name:
            return 'Spotify'
        elif 'soundcloud' in service_name:
            return 'SoundCloud'
        else:
            return 'Other'


# Global JAP service instance
jap_service = JAPService()

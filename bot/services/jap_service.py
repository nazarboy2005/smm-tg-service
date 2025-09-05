"""
JAP (Just Another Panel) API Service
Integrates with JAP to fetch real services and manage orders
"""
import aiohttp
import asyncio
from typing import List, Dict, Optional, Any
from loguru import logger
from bot.config import settings


class JAPService:
    """Service for interacting with Just Another Panel (JAP) API"""
    
    def __init__(self):
        self.api_url = "https://justanotherpanel.com/api/v2"
        self.api_key = getattr(settings, 'jap_api_key', None)
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key:
            logger.warning("JAP API key not configured - JAP services will be unavailable")
    
    async def _make_request(self, action: str, **params) -> Dict[str, Any]:
        """Make a request to the JAP API"""
        if not self.api_key:
            logger.warning("JAP API key not configured")
            return {"error": "JAP API key not configured"}
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Prepare request parameters
            request_params = {
                "key": self.api_key,
                "action": action,
                **params
            }
            
            logger.debug(f"Making JAP API request: {action}")
            
            async with self.session.post(self.api_url, data=request_params) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.debug(f"JAP API response: {result}")
                    return result
                else:
                    logger.error(f"JAP API request failed with status {response.status}")
                    return {"error": f"HTTP {response.status}"}
                    
        except Exception as e:
            logger.error(f"Error making JAP API request: {e}")
            return {"error": str(e)}
    
    async def get_services(self) -> List[Dict[str, Any]]:
        """Fetch all available services from JAP, extracts platform and service_type"""
        try:
            if not self.api_key:
                logger.warning("JAP API key not configured - returning empty services list")
                return []

            result = await self._make_request("services")

            if "error" in result:
                logger.error(f"Error fetching JAP services: {result['error']}")
                return []

            # JAP API returns a list directly, not a dict with 'services' key
            if isinstance(result, list):
                services = result
            elif isinstance(result, dict):
                services = result.get("services", [])
            else:
                logger.error(f"Unexpected result type from JAP API: {type(result)}")
                return []

            enhanced_services = []

            for service in services:
                # Extract platform and service type from service name
                service_name = service.get("name", "").lower()
                platform = self._extract_platform(service_name)
                service_type = self._extract_service_type(service_name)

                enhanced_service = {
                    **service,
                    "platform": platform,
                    "service_type": service_type
                }
                enhanced_services.append(enhanced_service)

            logger.info(f"Successfully fetched {len(enhanced_services)} services from JAP")
            return enhanced_services

        except Exception as e:
            logger.error(f"Error getting JAP services: {e}")
            return []
    
    def _extract_platform(self, service_name: str) -> str:
        """Extract platform from service name (e.g., instagram, youtube)"""
        platforms = [
            "instagram", "youtube", "tiktok", "twitter", "facebook", 
            "telegram", "linkedin", "snapchat", "pinterest", "reddit",
            "twitch", "discord", "spotify", "apple", "google", "amazon"
        ]
        
        for platform in platforms:
            if platform in service_name:
                return platform
        
        return "other"
    
    def _extract_service_type(self, service_name: str) -> str:
        """Extract service type from service name (e.g., followers, likes)"""
        service_types = [
            "followers", "likes", "views", "comments", "shares",
            "subscribers", "watches", "plays", "downloads", "reviews",
            "ratings", "votes", "clicks", "impressions", "engagement"
        ]
        
        for service_type in service_types:
            if service_type in service_name:
                return service_type
        
        return "other"
    
    async def get_services_by_platform(self, platform: str) -> List[Dict[str, Any]]:
        """Get services filtered by platform"""
        try:
            all_services = await self.get_services()
            return [service for service in all_services if service.get("platform") == platform]
        except Exception as e:
            logger.error(f"Error getting services by platform {platform}: {e}")
            return []
    
    async def get_services_by_type(self, service_type: str) -> List[Dict[str, Any]]:
        """Get services filtered by service type"""
        try:
            all_services = await self.get_services()
            return [service for service in all_services if service.get("service_type") == service_type]
        except Exception as e:
            logger.error(f"Error getting services by type {service_type}: {e}")
            return []
    
    async def add_order(self, service_id: int, link: str, quantity: int, 
                        runs: Optional[int] = None, interval: Optional[int] = None) -> Dict[str, Any]:
        """Add new order to JAP"""
        try:
            if not self.api_key:
                return {"error": "JAP API key not configured"}
            
            params = {
                "service": service_id,
                "link": link,
                "quantity": quantity
            }
            
            if runs:
                params["runs"] = runs
            if interval:
                params["interval"] = interval
            
            result = await self._make_request("add", **params)
            
            if "error" in result:
                logger.error(f"Error adding JAP order: {result['error']}")
                return result
            
            logger.info(f"Successfully added JAP order: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error adding JAP order: {e}")
            return {"error": str(e)}
    
    async def get_order_status(self, order_id: int) -> Dict[str, Any]:
        """Get order status from JAP"""
        try:
            if not self.api_key:
                return {"error": "JAP API key not configured"}
            
            result = await self._make_request("status", order=order_id)
            
            if "error" in result:
                logger.error(f"Error getting JAP order status: {result['error']}")
                return result
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting JAP order status: {e}")
            return {"error": str(e)}
    
    async def get_balance(self) -> Dict[str, Any]:
        """Get JAP account balance"""
        try:
            if not self.api_key:
                return {"error": "JAP API key not configured"}
            
            result = await self._make_request("balance")
            
            if "error" in result:
                logger.error(f"Error getting JAP balance: {result['error']}")
                return result
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting JAP balance: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """Close HTTP session"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
        except Exception as e:
            logger.error(f"Error closing JAP service session: {e}")


# Global JAP service instance
jap_service = JAPService()

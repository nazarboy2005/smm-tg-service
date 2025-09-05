"""
Admin Service Management System
Allows admins to control JAP services availability for users
"""
import json
from typing import List, Dict, Optional, Any, Set
from loguru import logger
from bot.database.db import db_manager
from bot.services.jap_service import jap_service


class AdminServiceManager:
    """Manages service availability and access control for users"""
    
    def __init__(self):
        self.service_settings_cache = {}
        self.user_access_cache = {}
        self.price_cache = {}
        self.cache_ttl = 300  # 5 minutes cache
        
        # Service filtering configuration
        self.allowed_telegram_services = {
            "7337", "7348", "7360", "7364", "7368", "7357", "7324", "7327", 
            "8619", "7328", "7762", "819", "1973", "7102", "7330", "1166", "8525"
        }
        self.disabled_platforms = {"instagram"}  # Platforms to disable
    
    async def initialize(self):
        """Initialize the admin service manager"""
        try:
            # Create service management tables if they don't exist
            await self._create_service_tables()
            logger.info("Admin service manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize admin service manager: {e}")
    
    async def _create_service_tables(self):
        """Create necessary database tables for service management"""
        try:
            # Service settings table
            await db_manager.execute("""
                CREATE TABLE IF NOT EXISTS service_settings (
                    id SERIAL PRIMARY KEY,
                    setting_key VARCHAR(100) UNIQUE NOT NULL,
                    setting_value TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Service access control table
            await db_manager.execute("""
                CREATE TABLE IF NOT EXISTS service_access_control (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    service_id INTEGER,
                    service_type VARCHAR(50),
                    platform VARCHAR(50),
                    is_active BOOLEAN DEFAULT true,
                    access_level VARCHAR(20) DEFAULT 'full',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, service_id),
                    UNIQUE(user_id, service_type, platform)
                )
            """)
            
            # Service pricing table
            await db_manager.execute("""
                CREATE TABLE IF NOT EXISTS service_pricing (
                    id SERIAL PRIMARY KEY,
                    service_id INTEGER NOT NULL,
                    platform VARCHAR(50),
                    service_type VARCHAR(50),
                    jap_price_usd DECIMAL(10,4) NOT NULL,
                    custom_price_usd DECIMAL(10,4),
                    custom_price_coins INTEGER,
                    markup_percentage DECIMAL(5,2) DEFAULT 0,
                    min_markup_usd DECIMAL(10,4) DEFAULT 0,
                    max_markup_usd DECIMAL(10,4) DEFAULT 999.99,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(service_id)
                )
            """)
            
            # Service categories table
            await db_manager.execute("""
                CREATE TABLE IF NOT EXISTS service_categories (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    platform VARCHAR(50),
                    is_active BOOLEAN DEFAULT true,
                    sort_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Cached services table - stores approved services from JAP
            await db_manager.execute("""
                CREATE TABLE IF NOT EXISTS cached_services (
                    id SERIAL PRIMARY KEY,
                    service_id INTEGER UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    platform VARCHAR(50),
                    service_type VARCHAR(50),
                    rate DECIMAL(10,4),
                    min_quantity INTEGER,
                    max_quantity INTEGER,
                    dripfeed BOOLEAN DEFAULT false,
                    refill BOOLEAN DEFAULT false,
                    cancel BOOLEAN DEFAULT false,
                    category TEXT,
                    is_approved BOOLEAN DEFAULT false,
                    is_active BOOLEAN DEFAULT true,
                    approved_by BIGINT,
                    approved_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Initialize default settings
            await self._initialize_default_settings()
            
            # Initialize cache with approved Telegram services
            await self._initialize_approved_services()
            
        except Exception as e:
            logger.error(f"Error creating service tables: {e}")
            raise
    
    async def _initialize_default_settings(self):
        """Initialize default service settings"""
        try:
            default_settings = [
                ("global_services_enabled", "true", "Enable/disable all JAP services globally"),
                ("default_user_access", "full", "Default access level for new users (full/limited/restricted)"),
                ("auto_sync_jap_services", "true", "Automatically sync services from JAP API"),
                ("service_cache_duration", "300", "Service cache duration in seconds"),
                ("max_services_per_user", "100", "Maximum number of services visible to each user"),
                ("enable_service_filtering", "true", "Enable service filtering by type and platform"),
                ("restricted_service_types", "[]", "Service types that are restricted by default"),
                ("restricted_platforms", "[]", "Platforms that are restricted by default"),
                ("default_markup_percentage", "20.0", "Default markup percentage for services"),
                ("coins_per_usd", "10000", "Conversion rate: coins per USD"),
                ("min_markup_usd", "0.01", "Minimum markup in USD"),
                ("max_markup_usd", "10.00", "Maximum markup in USD"),
                ("enable_custom_pricing", "true", "Enable custom pricing for services"),
                ("auto_update_pricing", "true", "Automatically update pricing when JAP prices change")
            ]
            
            for key, value, description in default_settings:
                await self._set_setting(key, value, description)
                
        except Exception as e:
            logger.error(f"Error initializing default settings: {e}")
    
    async def _initialize_approved_services(self):
        """Initialize cache with approved Telegram services"""
        try:
            # Check if cache is already initialized
            existing_count = await db_manager.fetchval("SELECT COUNT(*) FROM cached_services")
            if existing_count > 0:
                logger.info(f"Cache already initialized with {existing_count} services")
                return
            
            logger.info("Skipping JAP service initialization - services are disabled by default")
            logger.info("💡 Use /enable_jap command (admin only) to enable JAP services when needed")
            return
            
            # NOTE: JAP service fetching is now disabled by default
            # The following code is commented out to prevent automatic JAP fetching
            # logger.info("Initializing cache with approved Telegram services...")
            # 
            # # Get all services from JAP
            # all_jap_services = await jap_service.get_services()
            
            # Filter for approved Telegram services
            approved_services = []
            for service in all_jap_services:
                service_id = str(service.get("service", ""))
                if service_id in self.allowed_telegram_services:
                    approved_services.append(service)
            
            # Insert approved services into cache
            for service in approved_services:
                service_name = service.get("name", "").lower()
                platform = self._extract_platform_from_name(service_name)
                service_type = self._extract_service_type_from_name(service_name)
                
                await db_manager.execute("""
                    INSERT INTO cached_services (
                        service_id, name, platform, service_type, rate, min_quantity, 
                        max_quantity, dripfeed, refill, cancel, category, is_approved, 
                        is_active, approved_by, approved_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                """, 
                    int(service.get("service", 0)),
                    service.get("name", ""),
                    platform,
                    service_type,
                    float(service.get("rate", 0)),
                    int(service.get("min", 0)),
                    int(service.get("max", 0)),
                    bool(service.get("dripfeed", False)),
                    bool(service.get("refill", False)),
                    bool(service.get("cancel", False)),
                    service.get("category", ""),
                    True,  # Pre-approved
                    True,  # Active
                    1,     # System admin
                    "NOW()"  # Approved now
                )
            
            logger.info(f"Initialized cache with {len(approved_services)} approved Telegram services")
            
        except Exception as e:
            logger.error(f"Error initializing approved services: {e}")
    
    async def _set_setting(self, key: str, value: str, description: str = None):
        """Set a service setting"""
        try:
            await db_manager.execute("""
                INSERT INTO service_settings (setting_key, setting_value, description)
                VALUES ($1, $2, $3)
                ON CONFLICT (setting_key) 
                DO UPDATE SET 
                    setting_value = EXCLUDED.setting_value,
                    description = EXCLUDED.description,
                    updated_at = CURRENT_TIMESTAMP
            """, key, value, description or "")
            
        except Exception as e:
            logger.error(f"Error setting service setting {key}: {e}")
    
    async def get_setting(self, key: str, default: str = None) -> str:
        """Get a service setting"""
        try:
            result = await db_manager.fetchval("""
                SELECT setting_value FROM service_settings 
                WHERE setting_key = $1
            """, key)
            return result if result else default
        except Exception as e:
            logger.error(f"Error getting service setting {key}: {e}")
            return default
    
    async def get_all_services(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Get all available services from cache (approved services only)"""
        try:
            # Check if services are globally enabled
            if not await self.get_setting("global_services_enabled", "true") == "true":
                logger.info("Global services are disabled")
                return []
            
            # Get approved services from cache
            services = await self.get_approved_services()
            
            # Convert cached services to JAP-like format for compatibility
            formatted_services = []
            for service in services:
                formatted_service = {
                    "service": service["service_id"],
                    "name": service["name"],
                    "platform": service["platform"],
                    "service_type": service["service_type"],
                    "rate": str(service["rate"]),
                    "min": str(service["min_quantity"]),
                    "max": str(service["max_quantity"]),
                    "dripfeed": service["dripfeed"],
                    "refill": service["refill"],
                    "cancel": service["cancel"],
                    "category": service["category"]
                }
                formatted_services.append(formatted_service)
            
            if not include_inactive:
                # Filter out services that are globally restricted
                restricted_types = json.loads(await self.get_setting("restricted_service_types", "[]"))
                restricted_platforms = json.loads(await self.get_setting("restricted_platforms", "[]"))
                
                formatted_services = [
                    service for service in formatted_services
                    if (service.get("service_type") not in restricted_types and
                        service.get("platform") not in restricted_platforms)
                ]
            
            logger.info(f"Retrieved {len(formatted_services)} approved services from cache")
            return formatted_services
            
        except Exception as e:
            logger.error(f"Error getting all services: {e}")
            return []
    
    def _filter_services(self, services: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter services based on admin configuration"""
        filtered_services = []
        
        for service in services:
            service_id = str(service.get("service", ""))
            platform = service.get("platform", "").lower()
            
            # Skip disabled platforms
            if platform in self.disabled_platforms:
                logger.debug(f"Skipping {platform} service {service_id} - platform disabled")
                continue
            
            # For Telegram services, only allow specific service IDs
            if platform == "telegram":
                if service_id in self.allowed_telegram_services:
                    filtered_services.append(service)
                    logger.debug(f"Allowed Telegram service {service_id}")
                else:
                    logger.debug(f"Skipping Telegram service {service_id} - not in allowed list")
            else:
                # For other platforms, allow all services (except disabled platforms)
                filtered_services.append(service)
                logger.debug(f"Allowed {platform} service {service_id}")
        
        logger.info(f"Filtered {len(services)} services down to {len(filtered_services)} allowed services")
        return filtered_services
    
    def update_telegram_services(self, service_ids: List[str]):
        """Update the list of allowed Telegram service IDs"""
        self.allowed_telegram_services = set(service_ids)
        logger.info(f"Updated allowed Telegram services: {self.allowed_telegram_services}")
    
    def update_disabled_platforms(self, platforms: List[str]):
        """Update the list of disabled platforms"""
        self.disabled_platforms = set(platform.lower() for platform in platforms)
        logger.info(f"Updated disabled platforms: {self.disabled_platforms}")
    
    async def add_service_by_code(self, service_id: int, admin_user_id: int) -> Dict[str, Any]:
        """Add a new service by JAP service code"""
        try:
            # First, check if service already exists in cache
            existing = await db_manager.fetchrow(
                "SELECT * FROM cached_services WHERE service_id = $1", service_id
            )
            if existing:
                return {"success": False, "error": "Service already exists in cache"}
            
            # Get service details from JAP
            all_jap_services = await jap_service.get_services()
            jap_service_data = None
            
            for service in all_jap_services:
                if str(service.get("service", "")) == str(service_id):
                    jap_service_data = service
                    break
            
            if not jap_service_data:
                return {"success": False, "error": f"Service {service_id} not found in JAP"}
            
            # Extract platform and service type
            service_name = jap_service_data.get("name", "").lower()
            platform = self._extract_platform_from_name(service_name)
            service_type = self._extract_service_type_from_name(service_name)
            
            # Insert into cached services (not approved yet)
            await db_manager.execute("""
                INSERT INTO cached_services (
                    service_id, name, platform, service_type, rate, min_quantity, 
                    max_quantity, dripfeed, refill, cancel, category, is_approved, 
                    is_active, approved_by, approved_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            """, 
                service_id,
                jap_service_data.get("name", ""),
                platform,
                service_type,
                float(jap_service_data.get("rate", 0)),
                int(jap_service_data.get("min", 0)),
                int(jap_service_data.get("max", 0)),
                bool(jap_service_data.get("dripfeed", False)),
                bool(jap_service_data.get("refill", False)),
                bool(jap_service_data.get("cancel", False)),
                jap_service_data.get("category", ""),
                False,  # Not approved yet
                True,   # Active
                None,   # Not approved by anyone yet
                None    # Not approved yet
            )
            
            logger.info(f"Added service {service_id} to cache (pending approval)")
            return {
                "success": True, 
                "message": f"Service {service_id} added successfully. Awaiting admin approval.",
                "service": {
                    "id": service_id,
                    "name": jap_service_data.get("name", ""),
                    "platform": platform,
                    "service_type": service_type,
                    "rate": float(jap_service_data.get("rate", 0))
                }
            }
            
        except Exception as e:
            logger.error(f"Error adding service by code: {e}")
            return {"success": False, "error": str(e)}
    
    async def approve_service(self, service_id: int, admin_user_id: int) -> bool:
        """Approve a cached service"""
        try:
            result = await db_manager.execute("""
                UPDATE cached_services 
                SET is_approved = true, approved_by = $1, approved_at = CURRENT_TIMESTAMP
                WHERE service_id = $2
            """, admin_user_id, service_id)
            
            logger.info(f"Service {service_id} approved by admin {admin_user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error approving service: {e}")
            return False
    
    async def get_pending_services(self) -> List[Dict[str, Any]]:
        """Get services pending approval"""
        try:
            services = await db_manager.fetch("""
                SELECT * FROM cached_services 
                WHERE is_approved = false AND is_active = true
                ORDER BY created_at DESC
            """)
            return [dict(service) for service in services]
        except Exception as e:
            logger.error(f"Error getting pending services: {e}")
            return []
    
    async def get_approved_services(self, platform: str = None) -> List[Dict[str, Any]]:
        """Get approved services from cache"""
        try:
            if platform:
                services = await db_manager.fetch("""
                    SELECT * FROM cached_services 
                    WHERE is_approved = true AND is_active = true AND platform = $1
                    ORDER BY platform, service_type, name
                """, platform)
            else:
                services = await db_manager.fetch("""
                    SELECT * FROM cached_services 
                    WHERE is_approved = true AND is_active = true
                    ORDER BY platform, service_type, name
                """)
            return [dict(service) for service in services]
        except Exception as e:
            logger.error(f"Error getting approved services: {e}")
            return []
    
    def _extract_platform_from_name(self, service_name: str) -> str:
        """Extract platform from service name"""
        platforms = [
            "instagram", "youtube", "tiktok", "twitter", "facebook", 
            "telegram", "linkedin", "snapchat", "pinterest", "reddit",
            "twitch", "discord", "spotify", "apple", "google", "amazon"
        ]
        
        for platform in platforms:
            if platform in service_name:
                return platform
        
        return "other"
    
    def _extract_service_type_from_name(self, service_name: str) -> str:
        """Extract service type from service name"""
        service_types = [
            "followers", "likes", "views", "comments", "shares",
            "subscribers", "watches", "plays", "downloads", "reviews",
            "ratings", "votes", "clicks", "impressions", "engagement"
        ]
        
        for service_type in service_types:
            if service_type in service_name:
                return service_type
        
        return "other"
    
    async def get_services_for_user(self, user_id: int, platform: str = None, 
                                   service_type: str = None) -> List[Dict[str, Any]]:
        """Get services available for a specific user"""
        try:
            # Get user's access level
            user_access = await self._get_user_access_level(user_id)
            
            if user_access == "restricted":
                return []
            
            # Get all available services
            all_services = await self.get_all_services()
            
            # Apply user-specific restrictions
            user_restrictions = await self._get_user_service_restrictions(user_id)
            
            filtered_services = []
            for service in all_services:
                service_id = service.get("id")
                service_platform = service.get("platform")
                service_type_name = service.get("service_type")
                
                # Check if service is restricted for this user
                if service_id in user_restrictions.get("blocked_services", []):
                    continue
                
                # Check platform and type filters
                if platform and service_platform != platform:
                    continue
                if service_type and service_type_name != service_type:
                    continue
                
                # Check if user has access to this service type/platform
                if not await self._check_user_service_access(user_id, service_id, service_type_name, service_platform):
                    continue
                
                # Add pricing information for users
                pricing_info = await self.get_service_pricing(service_id, for_admin=False)
                if pricing_info:
                    service["pricing"] = pricing_info
                
                filtered_services.append(service)
            
            # Limit services per user
            max_services = int(await self.get_setting("max_services_per_user", "100"))
            if len(filtered_services) > max_services:
                filtered_services = filtered_services[:max_services]
            
            return filtered_services
            
        except Exception as e:
            logger.error(f"Error getting services for user {user_id}: {e}")
            return []
    
    async def _get_user_access_level(self, user_id: int) -> str:
        """Get user's service access level"""
        try:
            # Check for specific user restrictions
            result = await db_manager.fetchrow("""
                SELECT access_level FROM service_access_control 
                WHERE user_id = $1 AND service_id IS NULL 
                AND service_type IS NULL AND platform IS NULL
                LIMIT 1
            """, user_id)
            
            if result:
                return result["access_level"]
            
            # Return default access level
            return await self.get_setting("default_user_access", "full")
            
        except Exception as e:
            logger.error(f"Error getting user access level: {e}")
            return "full"
    
    async def _get_user_service_restrictions(self, user_id: int) -> Dict[str, Any]:
        """Get user's service restrictions"""
        try:
            restrictions = {
                "blocked_services": [],
                "blocked_types": [],
                "blocked_platforms": []
            }
            
            # Get blocked services
            blocked_services = await db_manager.fetch("""
                SELECT service_id FROM service_access_control 
                WHERE user_id = $1 AND is_active = false AND service_id IS NOT NULL
            """, user_id)
            
            restrictions["blocked_services"] = [row["service_id"] for row in blocked_services]
            
            # Get blocked service types
            blocked_types = await db_manager.fetch("""
                SELECT service_type FROM service_access_control 
                WHERE user_id = $1 AND is_active = false AND service_type IS NOT NULL
            """, user_id)
            
            restrictions["blocked_types"] = [row["service_type"] for row in blocked_types]
            
            # Get blocked platforms
            blocked_platforms = await db_manager.fetch("""
                SELECT platform FROM service_access_control 
                WHERE user_id = $1 AND is_active = false AND platform IS NOT NULL
            """, user_id)
            
            restrictions["blocked_platforms"] = [row["platform"] for row in blocked_platforms]
            
            return restrictions
            
        except Exception as e:
            logger.error(f"Error getting user service restrictions: {e}")
            return {"blocked_services": [], "blocked_types": [], "blocked_platforms": []}
    
    async def _check_user_service_access(self, user_id: int, service_id: int, 
                                       service_type: str, platform: str) -> bool:
        """Check if user has access to a specific service"""
        try:
            # Check service-specific access
            result = await db_manager.fetchrow("""
                SELECT is_active FROM service_access_control 
                WHERE user_id = $1 AND service_id = $2
            """, user_id, service_id)
            
            if result:
                return result["is_active"]
            
            # Check service type access
            result = await db_manager.fetchrow("""
                SELECT is_active FROM service_access_control 
                WHERE user_id = $1 AND service_type = $2 AND platform = $3
            """, user_id, service_type, platform)
            
            if result:
                return result["is_active"]
            
            # Check platform access
            result = await db_manager.fetchrow("""
                SELECT is_active FROM service_access_control 
                WHERE user_id = $1 AND platform = $2 AND service_type IS NULL
            """, user_id, platform)
            
            if result:
                return result["is_active"]
            
            # Default: allow access
            return True
            
        except Exception as e:
            logger.error(f"Error checking user service access: {e}")
            return True
    
    # Admin Management Methods
    
    async def set_service_availability(self, service_id: int, is_active: bool, 
                                     user_id: Optional[int] = None) -> bool:
        """Set service availability for all users or specific user"""
        try:
            if user_id:
                # User-specific setting
                await db_manager.execute("""
                    INSERT INTO service_access_control (user_id, service_id, is_active)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (user_id, service_id) 
                    DO UPDATE SET is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP
                """, user_id, service_id, is_active)
            else:
                # Global setting - apply to all users
                await db_manager.execute("""
                    INSERT INTO service_access_control (user_id, service_id, is_active)
                    SELECT u.id, $1, $2
                    FROM users u
                    ON CONFLICT (user_id, service_id) 
                    DO UPDATE SET is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP
                """, service_id, is_active)
            
            # Clear cache
            self._clear_cache()
            
            logger.info(f"Service {service_id} availability set to {is_active} for {'user ' + str(user_id) if user_id else 'all users'}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting service availability: {e}")
            return False
    
    async def set_service_type_availability(self, service_type: str, platform: str, 
                                          is_active: bool, user_id: Optional[int] = None) -> bool:
        """Set service type availability for all users or specific user"""
        try:
            if user_id:
                # User-specific setting
                await db_manager.execute("""
                    INSERT INTO service_access_control (user_id, service_type, platform, is_active)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (user_id, service_type, platform) 
                    DO UPDATE SET is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP
                """, user_id, service_type, platform, is_active)
            else:
                # Global setting - apply to all users
                await db_manager.execute("""
                    INSERT INTO service_access_control (user_id, service_type, platform, is_active)
                    SELECT u.id, $1, $2, $3
                    FROM users u
                    ON CONFLICT (user_id, service_type, platform) 
                    DO UPDATE SET is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP
                """, service_type, platform, is_active)
            
            # Clear cache
            self._clear_cache()
            
            logger.info(f"Service type {service_type} on {platform} availability set to {is_active} for {'user ' + str(user_id) if user_id else 'all users'}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting service type availability: {e}")
            return False
    
    async def set_platform_availability(self, platform: str, is_active: bool, 
                                      user_id: Optional[int] = None) -> bool:
        """Set platform availability for all users or specific user"""
        try:
            if user_id:
                # User-specific setting
                await db_manager.execute("""
                    INSERT INTO service_access_control (user_id, platform, is_active)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (user_id, platform) 
                    DO UPDATE SET is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP
                """, user_id, platform, is_active)
            else:
                # Global setting - apply to all users
                await db_manager.execute("""
                    INSERT INTO service_access_control (user_id, platform, is_active)
                    SELECT u.id, $1, $2
                    FROM users u
                    ON CONFLICT (user_id, platform) 
                    DO UPDATE SET is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP
                """, platform, is_active)
            
            # Clear cache
            self._clear_cache()
            
            logger.info(f"Platform {platform} availability set to {is_active} for {'user ' + str(user_id) if user_id else 'all users'}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting platform availability: {e}")
            return False
    
    async def set_user_access_level(self, user_id: int, access_level: str) -> bool:
        """Set user's overall service access level"""
        try:
            await db_manager.execute("""
                INSERT INTO service_access_control (user_id, access_level)
                VALUES ($1, $2)
                ON CONFLICT (user_id) 
                DO UPDATE SET access_level = EXCLUDED.access_level, updated_at = CURRENT_TIMESTAMP
            """, user_id, access_level)
            
            # Clear cache
            self._clear_cache()
            
            logger.info(f"User {user_id} access level set to {access_level}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting user access level: {e}")
            return False
    
    async def get_service_statistics(self) -> Dict[str, Any]:
        """Get comprehensive service statistics for admin dashboard"""
        try:
            stats = {}
            
            # Total services
            all_services = await self.get_all_services(include_inactive=True)
            stats["total_services"] = len(all_services)
            
            # Services by platform
            platforms = {}
            for service in all_services:
                platform = service.get("platform", "other")
                if platform not in platforms:
                    platforms[platform] = 0
                platforms[platform] += 1
            stats["services_by_platform"] = platforms
            
            # Services by type
            service_types = {}
            for service in all_services:
                service_type = service.get("service_type", "other")
                if service_type not in service_types:
                    service_types[service_type] = 0
                service_types[service_type] += 1
            stats["services_by_type"] = service_types
            
            # Active services
            active_services = await self.get_all_services(include_inactive=False)
            stats["active_services"] = len(active_services)
            
            # User access statistics
            user_stats = await db_manager.fetchrow("""
                SELECT 
                    COUNT(DISTINCT user_id) as total_users,
                    COUNT(CASE WHEN access_level = 'full' THEN 1 END) as full_access_users,
                    COUNT(CASE WHEN access_level = 'limited' THEN 1 END) as limited_access_users,
                    COUNT(CASE WHEN access_level = 'restricted' THEN 1 END) as restricted_users
                FROM service_access_control 
                WHERE service_id IS NULL AND service_type IS NULL AND platform IS NULL
            """)
            
            if user_stats:
                stats["user_access_stats"] = dict(user_stats)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting service statistics: {e}")
            return {}

    # Pricing Management Methods
    
    async def set_service_price(self, service_id: int, custom_price_usd: float, 
                               markup_percentage: float = None) -> bool:
        """Set custom price for a specific service"""
        try:
            # Get JAP price for this service
            all_services = await jap_service.get_services()
            jap_service_data = None
            for service in all_services:
                if service.get("id") == service_id:
                    jap_service_data = service
                    break
            
            if not jap_service_data:
                logger.error(f"Service {service_id} not found in JAP")
                return False
            
            jap_price_usd = jap_service_data.get("rate", 0)
            platform = jap_service_data.get("platform", "other")
            service_type = jap_service_data.get("service_type", "other")
            
            # Calculate markup if not provided
            if markup_percentage is None:
                default_markup = float(await self.get_setting("default_markup_percentage", "20.0"))
                markup_percentage = default_markup
            
            # Calculate custom price in coins
            coins_per_usd = int(await self.get_setting("coins_per_usd", "10000"))
            custom_price_coins = int(custom_price_usd * coins_per_usd)
            
            # Insert or update pricing
            await db_manager.execute("""
                INSERT INTO service_pricing (
                    service_id, platform, service_type, jap_price_usd, 
                    custom_price_usd, custom_price_coins, markup_percentage
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (service_id) 
                DO UPDATE SET 
                    custom_price_usd = EXCLUDED.custom_price_usd,
                    custom_price_coins = EXCLUDED.custom_price_coins,
                    markup_percentage = EXCLUDED.markup_percentage,
                    updated_at = CURRENT_TIMESTAMP
            """, service_id, platform, service_type, jap_price_usd, 
                 custom_price_usd, custom_price_coins, markup_percentage)
            
            # Clear price cache
            self.price_cache.clear()
            
            logger.info(f"Service {service_id} price set to ${custom_price_usd} (markup: {markup_percentage}%)")
            return True
            
        except Exception as e:
            logger.error(f"Error setting service price: {e}")
            return False
    
    async def get_service_pricing(self, service_id: int, for_admin: bool = False) -> Dict[str, Any]:
        """Get pricing information for a service"""
        try:
            # Get custom pricing from database
            pricing_result = await db_manager.fetchrow("""
                SELECT * FROM service_pricing WHERE service_id = $1
            """, service_id)
            
            # Get JAP service data
            all_services = await jap_service.get_services()
            jap_service_data = None
            for service in all_services:
                if service.get("id") == service_id:
                    jap_service_data = service
                    break
            
            if not jap_service_data:
                return {}
            
            jap_price_usd = jap_service_data.get("rate", 0)
            platform = jap_service_data.get("platform", "other")
            service_type = jap_service_data.get("service_type", "other")
            
            # Get conversion rate
            coins_per_usd = int(await self.get_setting("coins_per_usd", "10000"))
            
            if pricing_result:
                # Custom pricing exists
                custom_price_usd = float(pricing_result["custom_price_usd"])
                custom_price_coins = int(pricing_result["custom_price_coins"])
                markup_percentage = float(pricing_result["markup_percentage"])
                
                pricing_info = {
                    "service_id": service_id,
                    "platform": platform,
                    "service_type": service_type,
                    "jap_price_usd": jap_price_usd,
                    "custom_price_usd": custom_price_usd,
                    "custom_price_coins": custom_price_coins,
                    "markup_percentage": markup_percentage,
                    "price_difference_usd": custom_price_usd - jap_price_usd,
                    "price_difference_percentage": ((custom_price_usd - jap_price_usd) / jap_price_usd * 100) if jap_price_usd > 0 else 0
                }
                
                if for_admin:
                    # Show both JAP and custom prices to admin
                    pricing_info["display_price_usd"] = custom_price_usd
                    pricing_info["display_price_coins"] = custom_price_coins
                    pricing_info["show_jap_price"] = True
                else:
                    # Show only custom price to users
                    pricing_info["display_price_usd"] = custom_price_usd
                    pricing_info["display_price_coins"] = custom_price_coins
                    pricing_info["show_jap_price"] = False
                
                return pricing_info
            else:
                # No custom pricing, use JAP price
                default_markup = float(await self.get_setting("default_markup_percentage", "20.0"))
                custom_price_usd = jap_price_usd * (1 + default_markup / 100)
                custom_price_coins = int(custom_price_usd * coins_per_usd)
                
                pricing_info = {
                    "service_id": service_id,
                    "platform": platform,
                    "service_type": service_type,
                    "jap_price_usd": jap_price_usd,
                    "custom_price_usd": custom_price_usd,
                    "custom_price_coins": custom_price_coins,
                    "markup_percentage": default_markup,
                    "price_difference_usd": custom_price_usd - jap_price_usd,
                    "price_difference_percentage": default_markup,
                    "is_default_pricing": True
                }
                
                if for_admin:
                    pricing_info["display_price_usd"] = custom_price_usd
                    pricing_info["display_price_coins"] = custom_price_coins
                    pricing_info["show_jap_price"] = True
                else:
                    pricing_info["display_price_usd"] = custom_price_usd
                    pricing_info["display_price_coins"] = custom_price_coins
                    pricing_info["show_jap_price"] = False
                
                return pricing_info
                
        except Exception as e:
            logger.error(f"Error getting service pricing: {e}")
            return {}
    
    async def calculate_order_price(self, service_id: int, quantity: int) -> Dict[str, Any]:
        """Calculate order price using custom pricing"""
        try:
            pricing_info = await self.get_service_pricing(service_id, for_admin=False)
            
            if not pricing_info:
                return {"success": False, "message": "Service pricing not found"}
            
            custom_price_usd = pricing_info.get("custom_price_usd", 0)
            custom_price_coins = pricing_info.get("custom_price_coins", 0)
            
            if custom_price_usd <= 0:
                return {"success": False, "message": "Invalid service price"}
            
            # Calculate total price
            total_price_usd = (custom_price_usd * quantity) / 1000  # JAP prices are per 1000
            total_price_coins = int(total_price_usd * int(await self.get_setting("coins_per_usd", "10000")))
            
            return {
                "success": True,
                "service_id": service_id,
                "quantity": quantity,
                "price_per_1000_usd": custom_price_usd,
                "price_per_1000_coins": custom_price_coins,
                "total_price_usd": total_price_usd,
                "total_price_coins": total_price_coins,
                "pricing_type": "custom" if pricing_info.get("custom_price_usd") != pricing_info.get("jap_price_usd") else "default"
            }
            
        except Exception as e:
            logger.error(f"Error calculating order price: {e}")
            return {"success": False, "message": str(e)}
    
    async def bulk_update_pricing(self, platform: str = None, service_type: str = None, 
                                 markup_percentage: float = None) -> Dict[str, Any]:
        """Bulk update pricing for multiple services"""
        try:
            if markup_percentage is None:
                markup_percentage = float(await self.get_setting("default_markup_percentage", "20.0"))
            
            # Get services to update
            all_services = await jap_service.get_services()
            services_to_update = []
            
            for service in all_services:
                if platform and service.get("platform") != platform:
                    continue
                if service_type and service.get("service_type") != service_type:
                    continue
                services_to_update.append(service)
            
            if not services_to_update:
                return {"success": False, "message": "No services found for update"}
            
            # Update pricing for each service
            updated_count = 0
            failed_count = 0
            
            for service in services_to_update:
                service_id = service.get("id")
                jap_price_usd = service.get("rate", 0)
                
                if jap_price_usd > 0:
                    custom_price_usd = jap_price_usd * (1 + markup_percentage / 100)
                    success = await self.set_service_price(service_id, custom_price_usd, markup_percentage)
                    
                    if success:
                        updated_count += 1
                    else:
                        failed_count += 1
            
            return {
                "success": True,
                "updated_count": updated_count,
                "failed_count": failed_count,
                "total_services": len(services_to_update),
                "markup_percentage": markup_percentage
            }
            
        except Exception as e:
            logger.error(f"Error in bulk pricing update: {e}")
            return {"success": False, "message": str(e)}
    
    async def get_pricing_statistics(self) -> Dict[str, Any]:
        """Get pricing statistics for admin dashboard"""
        try:
            stats = {}
            
            # Get all pricing records
            pricing_records = await db_manager.fetchrow("""
                SELECT 
                    COUNT(*) as total_priced_services,
                    COUNT(CASE WHEN custom_price_usd > jap_price_usd THEN 1 END) as markup_services,
                    COUNT(CASE WHEN custom_price_usd < jap_price_usd THEN 1 END) as discount_services,
                    COUNT(CASE WHEN custom_price_usd = jap_price_usd THEN 1 END) as same_price_services,
                    AVG(markup_percentage) as avg_markup_percentage,
                    MIN(markup_percentage) as min_markup_percentage,
                    MAX(markup_percentage) as max_markup_percentage
                FROM service_pricing
            """)
            
            if pricing_records:
                stats["pricing"] = dict(pricing_records[0])
            
            # Get pricing by platform
            platform_pricing = await db_manager.fetch("""
                SELECT 
                    platform,
                    COUNT(*) as service_count,
                    AVG(markup_percentage) as avg_markup
                FROM service_pricing 
                GROUP BY platform
            """)
            
            stats["platform_pricing"] = [dict(record) for record in platform_pricing]
            
            # Get pricing by service type
            type_pricing = await db_manager.fetch("""
                SELECT 
                    service_type,
                    COUNT(*) as service_count,
                    AVG(markup_percentage) as avg_markup
                FROM service_pricing 
                GROUP BY service_type
            """)
            
            stats["type_pricing"] = [dict(record) for record in type_pricing]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting pricing statistics: {e}")
            return {}
    
    def _clear_cache(self):
        """Clear service cache"""
        self.service_settings_cache.clear()
        self.user_access_cache.clear()
        self.price_cache.clear()
    
    async def close(self):
        """Close the admin service manager"""
        try:
            self._clear_cache()
            logger.info("Admin service manager closed")
        except Exception as e:
            logger.error(f"Error closing admin service manager: {e}")


# Global admin service manager instance
admin_service_manager = AdminServiceManager()

"""
System status monitoring and health checks
"""
import asyncio
import time
from typing import Dict, Any, Optional
from loguru import logger
from bot.database.db import db_manager
from bot.config import settings


class SystemStatus:
    """System status monitor"""
    
    def __init__(self):
        self.start_time = time.time()
        self.last_health_check = None
        self.health_status = {}
    
    async def check_database_health(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            start_time = time.time()
            result = await db_manager.fetchval("SELECT 1")
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            if result == 1:
                return {
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "error": None
                }
            else:
                return {
                    "status": "unhealthy",
                    "response_time_ms": round(response_time, 2),
                    "error": "Unexpected database response"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "response_time_ms": None,
                "error": str(e)
            }
    
    async def check_system_resources(self) -> Dict[str, Any]:
        """Check system resources"""
        try:
            import psutil
            
            # Get system information
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "status": "healthy",
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "error": None
            }
        except ImportError:
            return {
                "status": "unknown",
                "error": "psutil not available"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_bot_configuration(self) -> Dict[str, Any]:
        """Check bot configuration"""
        try:
            config_status = {
                "status": "healthy",
                "checks": {}
            }
            
            # Check required settings
            required_settings = [
                "bot_token",
                "database_url",
                "jap_api_key",
                "jap_api_url"
            ]
            
            for setting in required_settings:
                value = getattr(settings, setting, None)
                config_status["checks"][setting] = {
                    "configured": value is not None and value != "",
                    "value_length": len(str(value)) if value else 0
                }
            
            # Check if all required settings are configured
            all_configured = all(
                config_status["checks"][setting]["configured"] 
                for setting in required_settings
            )
            
            if not all_configured:
                config_status["status"] = "unhealthy"
                config_status["error"] = "Some required settings are not configured"
            
            return config_status
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def get_uptime(self) -> Dict[str, Any]:
        """Get system uptime"""
        try:
            uptime_seconds = time.time() - self.start_time
            
            # Convert to human readable format
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            seconds = int(uptime_seconds % 60)
            
            return {
                "status": "healthy",
                "uptime_seconds": uptime_seconds,
                "uptime_human": f"{days}d {hours}h {minutes}m {seconds}s",
                "start_time": self.start_time,
                "error": None
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check"""
        try:
            logger.info("Running system health check...")
            
            # Run all health checks in parallel
            tasks = [
                self.check_database_health(),
                self.check_system_resources(),
                self.check_bot_configuration(),
                self.get_uptime()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            health_status = {
                "timestamp": time.time(),
                "overall_status": "healthy",
                "checks": {
                    "database": results[0] if not isinstance(results[0], Exception) else {"status": "unhealthy", "error": str(results[0])},
                    "system_resources": results[1] if not isinstance(results[1], Exception) else {"status": "unhealthy", "error": str(results[1])},
                    "configuration": results[2] if not isinstance(results[2], Exception) else {"status": "unhealthy", "error": str(results[2])},
                    "uptime": results[3] if not isinstance(results[3], Exception) else {"status": "unhealthy", "error": str(results[3])}
                }
            }
            
            # Determine overall status
            unhealthy_checks = [
                check for check in health_status["checks"].values() 
                if check.get("status") != "healthy"
            ]
            
            if unhealthy_checks:
                health_status["overall_status"] = "unhealthy"
                health_status["unhealthy_checks"] = len(unhealthy_checks)
            else:
                health_status["overall_status"] = "healthy"
                health_status["unhealthy_checks"] = 0
            
            self.health_status = health_status
            self.last_health_check = time.time()
            
            logger.info(f"Health check completed. Overall status: {health_status['overall_status']}")
            return health_status
            
        except Exception as e:
            logger.error(f"Error running health check: {e}")
            return {
                "timestamp": time.time(),
                "overall_status": "unhealthy",
                "error": str(e),
                "checks": {}
            }
    
    def get_status_summary(self) -> str:
        """Get human-readable status summary"""
        if not self.health_status:
            return "❓ Status unknown - no health checks performed"
        
        status = self.health_status.get("overall_status", "unknown")
        unhealthy_count = self.health_status.get("unhealthy_checks", 0)
        
        if status == "healthy":
            return f"✅ System healthy ({unhealthy_count} issues)"
        elif status == "unhealthy":
            return f"❌ System unhealthy ({unhealthy_count} issues)"
        else:
            return f"❓ System status unknown ({unhealthy_count} issues)"


# Global system status instance
system_status = SystemStatus()

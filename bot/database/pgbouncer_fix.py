"""
Pgbouncer compatibility fixes for Railway deployment
"""
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine
from loguru import logger


def apply_pgbouncer_compatibility(engine: AsyncEngine):
    """Apply pgbouncer compatibility fixes to the engine"""
    
    @event.listens_for(engine.sync_engine, "connect")
    def set_pgbouncer_settings(dbapi_connection, connection_record):
        """Set pgbouncer-compatible settings on connection"""
        try:
            # Set session-level settings for pgbouncer compatibility
            cursor = dbapi_connection.cursor()
            
            # Disable statement cache
            cursor.execute("SET statement_cache_mode = 'none'")
            
            # Set application name
            cursor.execute("SET application_name = 'follower-tg-service'")
            
            # Set reasonable timeouts
            cursor.execute("SET statement_timeout = '30000'")  # 30 seconds
            cursor.execute("SET lock_timeout = '10000'")  # 10 seconds
            
            cursor.close()
            logger.debug("Applied pgbouncer compatibility settings")
            
        except Exception as e:
            logger.warning(f"Failed to apply pgbouncer settings: {e}")
    
    @event.listens_for(engine.sync_engine, "checkout")
    def reset_connection(dbapi_connection, connection_record, connection_proxy):
        """Reset connection settings on checkout"""
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("SET statement_cache_mode = 'none'")
            cursor.close()
        except Exception as e:
            logger.debug(f"Failed to reset connection settings: {e}")
    
    logger.info("Pgbouncer compatibility fixes applied to database engine")
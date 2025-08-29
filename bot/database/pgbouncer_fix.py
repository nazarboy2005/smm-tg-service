"""
PgBouncer compatibility fix for asyncpg
This module provides utilities to ensure complete pgbouncer compatibility
"""
import asyncpg
from sqlalchemy.dialects.postgresql import asyncpg as sqlalchemy_asyncpg
from sqlalchemy.engine.events import event
from sqlalchemy.ext.asyncio import AsyncEngine
from loguru import logger


def apply_pgbouncer_compatibility(engine: AsyncEngine):
    """
    Apply comprehensive pgbouncer compatibility fixes to an SQLAlchemy AsyncEngine
    """
    
    @event.listens_for(engine.sync_engine, "before_cursor_execute", retval=True)
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Disable prepared statements at the cursor level"""
        if hasattr(cursor, '_prepared_stmt_name'):
            cursor._prepared_stmt_name = None
        return statement, parameters
    
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Configure connection for pgbouncer compatibility"""
        if hasattr(dbapi_connection, 'execute'):
            try:
                # Disable prepared statements at connection level
                dbapi_connection._prepared_stmt_cache_size = 0
                dbapi_connection._prepared_stmt_name_func = None
                logger.debug("Applied pgbouncer compatibility settings to connection")
            except Exception as e:
                logger.warning(f"Could not apply some pgbouncer settings: {e}")


# Monkey patch asyncpg Connection to disable prepared statements
original_prepare = asyncpg.Connection.prepare

async def disabled_prepare(self, query, *args, **kwargs):
    """Override prepare method to prevent prepared statement creation"""
    logger.warning("Prepared statement creation blocked for pgbouncer compatibility")
    # Return a mock prepared statement that just executes directly
    class MockPreparedStatement:
        def __init__(self, connection, query):
            self.connection = connection
            self.query = query
        
        async def fetch(self, *args, **kwargs):
            return await self.connection.fetch(self.query, *args, **kwargs)
        
        async def fetchrow(self, *args, **kwargs):
            return await self.connection.fetchrow(self.query, *args, **kwargs)
        
        async def execute(self, *args, **kwargs):
            return await self.connection.execute(self.query, *args, **kwargs)
    
    return MockPreparedStatement(self, query)


def patch_asyncpg_for_pgbouncer():
    """
    Monkey patch asyncpg to be fully compatible with pgbouncer
    """
    # Override the prepare method to prevent prepared statement creation
    asyncpg.Connection.prepare = disabled_prepare
    logger.info("Applied asyncpg monkey patch for pgbouncer compatibility")


# Apply the patch on import
patch_asyncpg_for_pgbouncer()
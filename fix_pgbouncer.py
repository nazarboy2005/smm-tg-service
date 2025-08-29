#!/usr/bin/env python3
"""
Script to test and fix pgbouncer compatibility issues
Run this to test database connectivity without prepared statements
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.sql import text
from loguru import logger

from bot.config import settings


async def test_db_connection():
    """Test database connection with pgbouncer-compatible settings"""
    try:
        logger.info("Testing database connection with pgbouncer compatibility...")
        
        # Create engine with maximum pgbouncer compatibility
        engine = create_async_engine(
            settings.database_url,
            echo=True,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=3,
            max_overflow=5,
            # Maximum pgbouncer compatibility
            connect_args={
                "statement_cache_size": 0,
                "prepared_statement_cache_size": 0,
                "command_timeout": 30,
            },
            strategy='plain',  # Force plain strategy
        )
        
        # Test basic connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            test_value = result.scalar()
            logger.info(f"Basic connection test: {test_value}")
        
        # Test session-based queries
        async_session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session_maker() as session:
            # Test a simple query that would normally use prepared statements
            result = await session.execute(text("SELECT COUNT(*) FROM information_schema.tables"))
            count = result.scalar()
            logger.info(f"Table count query: {count}")
            
            # Test parameterized query
            result = await session.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = :schema LIMIT 5"),
                {"schema": "public"}
            )
            tables = result.fetchall()
            logger.info(f"Found tables: {[row[0] for row in tables]}")
        
        await engine.dispose()
        logger.success("✅ Database connection test successful! pgbouncer compatibility confirmed.")
        
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
        logger.error("This indicates pgbouncer compatibility issues still exist.")
        raise


if __name__ == "__main__":
    asyncio.run(test_db_connection())
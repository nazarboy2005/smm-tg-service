"""
Database connection and session management
"""
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from loguru import logger

from bot.config import settings
from bot.database.models import Base


class DatabaseManager:
    """Database connection manager"""
    
    def __init__(self):
        self.engine = None
        self.async_session_maker = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connection"""
        if self._initialized:
            return
        
        try:
            # Create async engine with proper connection args for pgbouncer compatibility
            self.engine = create_async_engine(
                settings.database_url,
                echo=settings.environment == "development",
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_size=10,
                max_overflow=20,
                # Disable all statement caching for pgbouncer compatibility
                connect_args={
                    "server_settings": {
                        "application_name": "follower-tg-service",
                        "statement_timeout": "60000",  # 60 seconds
                        "lock_timeout": "30000",  # 30 seconds
                    },
                    "statement_cache_size": 0,  # Disable statement cache
                    "prepared_statement_cache_size": 0,  # Disable prepared statement cache
                    "command_timeout": 60,
                    # Additional pgbouncer compatibility settings
                    "statement_cache_mode": "none",
                    "prepared_statement_name_func": None,
                }
            )
            
            # Create session maker
            self.async_session_maker = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            self._initialized = True
            logger.info("Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise
    
    async def create_tables(self):
        """Create all tables"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Test connection first
            async with self.engine.begin() as conn:
                # Test if tables already exist by checking if users table exists
                try:
                    result = await conn.execute(
                        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users')"
                    )
                    tables_exist = bool(result.scalar())
                except Exception:
                    # If we can't check, assume tables don't exist
                    tables_exist = False
                
                if not tables_exist:
                    await conn.run_sync(Base.metadata.create_all)
                    logger.info("Database tables created successfully")
                else:
                    logger.info("Database tables already exist, skipping creation")
                    
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            # Don't raise the error, just log it - tables might already exist
            logger.warning("Continuing without table creation - tables may already exist")
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        if not self._initialized:
            await self.initialize()
        
        async with self.async_session_maker() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()
    
    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")


# Global database manager instance
db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async for session in db_manager.get_session():
        yield session


async def init_db():
    """Initialize database and create tables"""
    await db_manager.initialize()
    await db_manager.create_tables()


async def close_db():
    """Close database connection"""
    await db_manager.close()

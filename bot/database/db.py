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
# Removed problematic pgbouncer_fix import that was causing AsyncEngine issues


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
            # Create async engine with complete pgbouncer compatibility
            # The database URL should already have statement_cache_size=0 from config validation
            self.engine = create_async_engine(
                settings.database_url,
                echo=settings.environment == "development",
                pool_pre_ping=True,
                pool_recycle=300,  # Shorter for pgbouncer compatibility
                pool_size=3,  # Small pool for pgbouncer
                max_overflow=5,  # Limited overflow for pgbouncer
                connect_args={
                    "command_timeout": 30,  # Reasonable timeout
                },
                # Disable query compilation caching for pgbouncer
                execution_options={
                    "compiled_cache": {},
                }
            )
            
            # Create session maker
            self.async_session_maker = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Pgbouncer compatibility is handled through URL parameters and connect_args
            
            self._initialized = True
            logger.info("Database connection initialized successfully with pgbouncer compatibility")
            
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


async def get_db_session() -> AsyncSession:
    """Get a single database session for handlers"""
    if not db_manager._initialized:
        await db_manager.initialize()
    
    return db_manager.async_session_maker()


async def init_db():
    """Initialize database and create tables"""
    await db_manager.initialize()
    await db_manager.create_tables()


async def close_db():
    """Close database connection"""
    await db_manager.close()

#!/usr/bin/env python3
"""
Debug script to isolate the database comparison error
"""
import asyncio
import sys
from bot.database.db import db_manager
from bot.database.models import User
from sqlalchemy import select
from loguru import logger

async def test_db():
    """Test database operations to isolate the error"""
    try:
        await db_manager.initialize()
        logger.info("Database initialized successfully")
        
        async for session in db_manager.get_session():
            try:
                # Test simple query that might trigger the error
                result = await session.execute(
                    select(User).where(User.telegram_id == 123456789)
                )
                user = result.scalar_one_or_none()
                logger.info(f"Query executed successfully, user: {user}")
                break
            except Exception as e:
                logger.error(f"Error in query: {e}")
                import traceback
                traceback.print_exc()
                break
                
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(test_db())

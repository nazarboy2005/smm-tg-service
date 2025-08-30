#!/usr/bin/env python3
"""
Script to update database structure for JAP API compatibility
"""
import asyncio
import sys
from loguru import logger

# Add the bot directory to the path
sys.path.insert(0, '.')

from bot.database.db import initialize, create_tables, get_db_session
from bot.database.models import Base
from bot.services.service_service import ServiceService

async def update_database():
    """Update database structure"""
    try:
        logger.info("🔧 Updating database structure for JAP API compatibility...")
        
        # Initialize database connection
        await initialize()
        logger.info("✅ Database connection initialized")
        
        # Create/update tables
        await create_tables()
        logger.info("✅ Database tables updated")
        
        # Test database connection
        db = await get_db_session()
        try:
            # Test basic database operations
            logger.info("🧪 Testing database operations...")
            
            # Test JAP balance update
            logger.info("📊 Updating JAP balance...")
            balance_updated = await ServiceService.update_jap_balance(db)
            if balance_updated:
                logger.info("✅ JAP balance updated successfully")
            else:
                logger.warning("⚠️ Could not update JAP balance (this is normal if JAP API is not configured)")
            
            # Test service fetching from JAP API
            logger.info("📋 Testing JAP service fetching...")
            services = await ServiceService.get_services_from_jap()
            if services:
                logger.info(f"✅ Successfully fetched {len(services)} services from JAP API")
                
                # Test syncing a few services to database
                logger.info("🔄 Testing service sync to database...")
                sync_success = await ServiceService.sync_services_from_jap(db)
                if sync_success:
                    logger.info("✅ Services synced to database successfully")
                else:
                    logger.warning("⚠️ Service sync failed (this may be normal)")
            else:
                logger.warning("⚠️ No services fetched from JAP API (this is normal if JAP API is not configured)")
            
            logger.info("✅ Database operations test completed")
            
        except Exception as e:
            logger.error(f"❌ Error during database operations test: {e}")
        finally:
            await db.close()
        
        logger.info("🎉 Database update completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating database: {e}")
        return False

async def main():
    """Main function"""
    try:
        logger.info("🚀 Starting database update...")
        
        success = await update_database()
        
        if success:
            logger.info("✅ Database update completed successfully!")
            logger.info("💡 The database is now ready for JAP API integration")
        else:
            logger.error("❌ Database update failed")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

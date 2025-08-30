#!/usr/bin/env python3
"""
Migration script to add missing columns for JAP API compatibility
"""
import asyncio
import sys
from loguru import logger

# Add the bot directory to the path
sys.path.insert(0, '.')

from bot.database.db import initialize, get_db_session

async def migrate_database():
    """Migrate database to add missing columns"""
    try:
        logger.info("🔧 Migrating database for JAP API compatibility...")
        
        # Initialize database connection
        await initialize()
        logger.info("✅ Database connection initialized")
        
        # Get database session
        db = await get_db_session()
        try:
            # Add missing columns to existing tables
            logger.info("📝 Adding missing columns to existing tables...")
            
            # Add jap_category_id to service_categories
            try:
                await db.execute("ALTER TABLE service_categories ADD COLUMN IF NOT EXISTS jap_category_id INTEGER")
                logger.info("✅ Added jap_category_id to service_categories")
            except Exception as e:
                logger.warning(f"Column jap_category_id might already exist: {e}")
            
            # Add missing columns to services table
            try:
                await db.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS service_type VARCHAR(100)")
                await db.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS jap_rate_usd FLOAT")
                await db.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS supports_refill BOOLEAN DEFAULT FALSE")
                await db.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS supports_cancel BOOLEAN DEFAULT FALSE")
                await db.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS supports_dripfeed BOOLEAN DEFAULT FALSE")
                await db.execute("ALTER TABLE services ADD COLUMN IF NOT EXISTS meta_data JSON")
                logger.info("✅ Added missing columns to services table")
            except Exception as e:
                logger.warning(f"Some columns might already exist: {e}")
            
            # Add missing columns to orders table
            try:
                await db.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS jap_service_id INTEGER")
                await db.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS charge_usd FLOAT")
                await db.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS jap_charge FLOAT")
                await db.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS jap_currency VARCHAR(10) DEFAULT 'USD'")
                await db.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS jap_status VARCHAR(50)")
                await db.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS meta_data JSON")
                await db.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS notes TEXT")
                logger.info("✅ Added missing columns to orders table")
            except Exception as e:
                logger.warning(f"Some columns might already exist: {e}")
            
            # Add missing columns to transactions table
            try:
                await db.execute("ALTER TABLE transactions ALTER COLUMN meta_data TYPE JSON USING meta_data::json")
                logger.info("✅ Updated meta_data column in transactions table")
            except Exception as e:
                logger.warning(f"meta_data column might already be JSON: {e}")
            
            # Create jap_balances table if it doesn't exist
            try:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS jap_balances (
                        id SERIAL PRIMARY KEY,
                        balance FLOAT NOT NULL,
                        currency VARCHAR(10) NOT NULL DEFAULT 'USD',
                        last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                logger.info("✅ Created jap_balances table")
            except Exception as e:
                logger.warning(f"jap_balances table might already exist: {e}")
            
            # Commit changes
            await db.commit()
            logger.info("✅ Database migration completed successfully")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Error during migration: {e}")
            return False
        finally:
            await db.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error migrating database: {e}")
        return False

async def main():
    """Main function"""
    try:
        logger.info("🚀 Starting database migration...")
        
        success = await migrate_database()
        
        if success:
            logger.info("✅ Database migration completed successfully!")
            logger.info("💡 The database is now fully compatible with JAP API")
        else:
            logger.error("❌ Database migration failed")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

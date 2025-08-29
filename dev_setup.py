#!/usr/bin/env python3
"""
Development setup script for SMM Bot
This script initializes the database, creates tables, and sets up default settings
"""
import asyncio
import sys
import os
from loguru import logger

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.config import settings
from bot.database.db import init_db, close_db
from bot.database.models import Base
from bot.services.settings_service import SettingsService
from bot.services.service_service import ServiceService
from bot.database.db import get_db


async def setup_database():
    """Initialize database and create tables"""
    try:
        logger.info("🔄 Initializing database...")
        
        # Initialize database connection
        await init_db()
        
        logger.info("✅ Database initialized successfully")
        
        # Initialize default settings
        logger.info("🔄 Setting up default settings...")
        async for db in get_db():
            success = await SettingsService.initialize_default_settings(db)
            if success:
                logger.info("✅ Default settings initialized")
            else:
                logger.warning("⚠️ Failed to initialize default settings")
            break
        
        # Test database connection
        logger.info("🔄 Testing database connection...")
        async for db in get_db():
            # Test a simple query
            from bot.services.user_service import UserService
            user_count = await UserService.get_users_count(db)
            logger.info(f"✅ Database connection test successful. Users count: {user_count}")
            break
        
        logger.info("🎉 Database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        raise
    finally:
        await close_db()


async def create_sample_data():
    """Create sample data for testing"""
    try:
        logger.info("🔄 Creating sample data...")
        
        async for db in get_db():
            # Create sample service categories
            from bot.database.models import ServiceCategory, Service
            
            # Check if categories already exist
            from sqlalchemy import select
            result = await db.execute(select(ServiceCategory))
            existing_categories = result.scalars().all()
            
            if not existing_categories:
                # Create sample categories
                categories = [
                    ServiceCategory(name="Instagram", description="Instagram services", sort_order=1),
                    ServiceCategory(name="YouTube", description="YouTube services", sort_order=2),
                    ServiceCategory(name="TikTok", description="TikTok services", sort_order=3),
                    ServiceCategory(name="Twitter", description="Twitter services", sort_order=4),
                    ServiceCategory(name="Facebook", description="Facebook services", sort_order=5),
                ]
                
                for category in categories:
                    db.add(category)
                
                await db.commit()
                logger.info("✅ Sample categories created")
                
                # Create sample services
                services = [
                    Service(
                        category_id=1,  # Instagram
                        jap_service_id=1,
                        name="Instagram Followers",
                        description="High-quality Instagram followers",
                        price_per_1000=1000,
                        min_quantity=100,
                        max_quantity=10000
                    ),
                    Service(
                        category_id=1,  # Instagram
                        jap_service_id=2,
                        name="Instagram Likes",
                        description="Instagram post likes",
                        price_per_1000=500,
                        min_quantity=50,
                        max_quantity=5000
                    ),
                    Service(
                        category_id=2,  # YouTube
                        jap_service_id=3,
                        name="YouTube Views",
                        description="YouTube video views",
                        price_per_1000=800,
                        min_quantity=100,
                        max_quantity=50000
                    ),
                    Service(
                        category_id=2,  # YouTube
                        jap_service_id=4,
                        name="YouTube Subscribers",
                        description="YouTube channel subscribers",
                        price_per_1000=2000,
                        min_quantity=10,
                        max_quantity=1000
                    ),
                ]
                
                for service in services:
                    db.add(service)
                
                await db.commit()
                logger.info("✅ Sample services created")
            else:
                logger.info("ℹ️ Sample data already exists, skipping...")
            break
        
        logger.info("🎉 Sample data setup completed!")
        
    except Exception as e:
        logger.error(f"❌ Sample data creation failed: {e}")
        raise


async def verify_setup():
    """Verify that the setup was successful"""
    try:
        logger.info("🔄 Verifying setup...")
        
        async for db in get_db():
            # Check settings
            coins_per_usd = await SettingsService.get_setting(db, "coins_per_usd", 1000)
            min_deposit = await SettingsService.get_setting(db, "min_deposit_usd", 1.0)
            max_deposit = await SettingsService.get_setting(db, "max_deposit_usd", 1000.0)
            
            logger.info(f"✅ Settings verified:")
            logger.info(f"   - Coins per USD: {coins_per_usd}")
            logger.info(f"   - Min deposit: ${min_deposit}")
            logger.info(f"   - Max deposit: ${max_deposit}")
            
            # Check categories
            from bot.database.models import ServiceCategory
            from sqlalchemy import select
            result = await db.execute(select(ServiceCategory))
            categories = result.scalars().all()
            logger.info(f"✅ Found {len(categories)} service categories")
            
            # Check services
            from bot.database.models import Service
            result = await db.execute(select(Service))
            services = result.scalars().all()
            logger.info(f"✅ Found {len(services)} services")
            
            break
        
        logger.info("🎉 Setup verification completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Setup verification failed: {e}")
        raise


async def main():
    """Main setup function"""
    logger.info("🚀 Starting SMM Bot development setup...")
    
    try:
        # Setup database
        await setup_database()
        
        # Create sample data
        await create_sample_data()
        
        # Verify setup
        await verify_setup()
        
        logger.info("🎉 Development setup completed successfully!")
        logger.info("You can now run the bot with: python main.py")
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

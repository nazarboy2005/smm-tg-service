#!/usr/bin/env python3
"""
Test script to verify service filtering is working correctly
"""
import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.services.admin_service import admin_service_manager
from bot.database.db import db_manager
from loguru import logger


async def test_service_filtering():
    """Test the service filtering functionality"""
    try:
        logger.info("🧪 Testing Service Filtering...")
        
        # Initialize database
        await db_manager.initialize()
        logger.info("✅ Database initialized")
        
        # Initialize admin service manager
        await admin_service_manager.initialize()
        logger.info("✅ Admin service manager initialized")
        
        # Get all services (should be filtered)
        all_services = await admin_service_manager.get_all_services()
        logger.info(f"📊 Total filtered services: {len(all_services)}")
        
        # Check Telegram services
        telegram_services = [s for s in all_services if s.get("platform") == "telegram"]
        logger.info(f"📱 Telegram services: {len(telegram_services)}")
        
        # Check Instagram services (should be 0)
        instagram_services = [s for s in all_services if s.get("platform") == "instagram"]
        logger.info(f"📸 Instagram services: {len(instagram_services)}")
        
        # Show allowed Telegram service IDs
        allowed_telegram_ids = [s.get("service") for s in telegram_services]
        logger.info(f"✅ Allowed Telegram service IDs: {allowed_telegram_ids}")
        
        # Verify only allowed services are present
        expected_telegram_ids = {
            "7337", "7348", "7360", "7364", "7368", "7357", "7324", "7327", 
            "8619", "7328", "7762", "819", "1973", "7102", "7330", "1166", "8525"
        }
        
        actual_telegram_ids = set(allowed_telegram_ids)
        
        if actual_telegram_ids.issubset(expected_telegram_ids):
            logger.info("✅ All Telegram services are from the allowed list")
        else:
            unexpected = actual_telegram_ids - expected_telegram_ids
            logger.warning(f"⚠️ Found unexpected Telegram services: {unexpected}")
        
        if len(instagram_services) == 0:
            logger.info("✅ Instagram services are properly disabled")
        else:
            logger.warning(f"⚠️ Found {len(instagram_services)} Instagram services (should be 0)")
        
        # Show platform distribution
        platform_counts = {}
        for service in all_services:
            platform = service.get("platform", "unknown")
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        logger.info("📊 Platform distribution:")
        for platform, count in sorted(platform_counts.items()):
            logger.info(f"  • {platform}: {count} services")
        
        logger.info("🎉 Service filtering test completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(test_service_filtering())

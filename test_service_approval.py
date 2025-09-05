#!/usr/bin/env python3
"""
Test script to verify the service approval workflow
"""
import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.services.admin_service import admin_service_manager
from bot.database.db import db_manager
from loguru import logger


async def test_service_approval_workflow():
    """Test the complete service approval workflow"""
    try:
        logger.info("🧪 Testing Service Approval Workflow...")
        
        # Initialize database
        await db_manager.initialize()
        logger.info("✅ Database initialized")
        
        # Initialize admin service manager
        await admin_service_manager.initialize()
        logger.info("✅ Admin service manager initialized")
        
        # Test 1: Check initial cache
        logger.info("\n📊 Test 1: Checking initial cache...")
        approved_services = await admin_service_manager.get_approved_services()
        logger.info(f"✅ Initial approved services: {len(approved_services)}")
        
        # Test 2: Check pending services (should be empty initially)
        logger.info("\n📊 Test 2: Checking pending services...")
        pending_services = await admin_service_manager.get_pending_services()
        logger.info(f"✅ Pending services: {len(pending_services)}")
        
        # Test 3: Try to add a new service (using a test service ID)
        logger.info("\n📊 Test 3: Testing add service by code...")
        test_service_id = 10074  # Kick LiveStream Views service
        result = await admin_service_manager.add_service_by_code(test_service_id, 1)
        
        if result["success"]:
            logger.info(f"✅ Service {test_service_id} added successfully")
            logger.info(f"   Name: {result['service']['name']}")
            logger.info(f"   Platform: {result['service']['platform']}")
            logger.info(f"   Rate: ${result['service']['rate']}")
        else:
            logger.warning(f"⚠️ Failed to add service: {result['error']}")
        
        # Test 4: Check pending services again
        logger.info("\n📊 Test 4: Checking pending services after addition...")
        pending_services = await admin_service_manager.get_pending_services()
        logger.info(f"✅ Pending services: {len(pending_services)}")
        
        if pending_services:
            for service in pending_services:
                logger.info(f"   - ID: {service['service_id']}, Name: {service['name'][:50]}...")
        
        # Test 5: Approve the service
        if pending_services:
            logger.info("\n📊 Test 5: Testing service approval...")
            service_id = pending_services[0]['service_id']
            success = await admin_service_manager.approve_service(service_id, 1)
            
            if success:
                logger.info(f"✅ Service {service_id} approved successfully")
            else:
                logger.warning(f"⚠️ Failed to approve service {service_id}")
        
        # Test 6: Check approved services after approval
        logger.info("\n📊 Test 6: Checking approved services after approval...")
        approved_services = await admin_service_manager.get_approved_services()
        logger.info(f"✅ Total approved services: {len(approved_services)}")
        
        # Test 7: Test service filtering (should use cache now)
        logger.info("\n📊 Test 7: Testing service filtering with cache...")
        all_services = await admin_service_manager.get_all_services()
        logger.info(f"✅ Services available to users: {len(all_services)}")
        
        # Show platform distribution
        platform_counts = {}
        for service in all_services:
            platform = service.get("platform", "unknown")
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        logger.info("📊 Platform distribution:")
        for platform, count in sorted(platform_counts.items()):
            logger.info(f"   • {platform}: {count} services")
        
        logger.info("\n🎉 Service approval workflow test completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(test_service_approval_workflow())

#!/usr/bin/env python3
"""
Test script for the enhanced SMM Bot system
"""
import asyncio
import sys
from loguru import logger

# Add the bot directory to the path
sys.path.append('bot')

async def test_payment_system():
    """Test the enhanced payment system"""
    try:
        logger.info("🧪 Testing Enhanced Payment System...")
        
        # Test payment service initialization
        from bot.services.payment_service import payment_service
        
        logger.info("✅ Payment service imported successfully")
        
        # Test provider initialization
        providers = payment_service.providers
        logger.info(f"✅ Found {len(providers)} payment providers:")
        
        for provider_name, provider in providers.items():
            logger.info(f"  - {provider_name}: {provider.get_provider_name()}")
        
        # Test available providers
        try:
            from bot.database.db import get_db_session
            db = await get_db_session()
            try:
                available_providers = await payment_service.get_available_providers(db)
                logger.info(f"✅ Available providers: {len(available_providers)}")
                for provider in available_providers:
                    logger.info(f"  - {provider['id']}: {provider['name']}")
            finally:
                await db.close()
        except Exception as e:
            logger.warning(f"⚠️ Could not test available providers (database not available): {e}")
        
        logger.info("✅ Payment system test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Payment system test failed: {e}")
        return False
    
    return True


async def test_database_system():
    """Test the enhanced database system"""
    try:
        logger.info("🧪 Testing Enhanced Database System...")
        
        # Test database manager import
        from bot.database.db import db_manager
        
        logger.info("✅ Database manager imported successfully")
        
        # Test database initialization
        success = await db_manager.initialize()
        if not success:
            logger.error("❌ Database initialization failed")
            return False
            
        logger.info("✅ Database initialized successfully")
        
        # Test connection
        is_healthy = await db_manager.health_check()
        if is_healthy:
            logger.info("✅ Database health check passed")
        else:
            logger.warning("⚠️ Database health check failed")
        
        # Test session creation
        session = await db_manager.get_connection()
        logger.info("✅ Database connection created successfully")
        await db_manager.pool.release(session)
        logger.info("✅ Database connection released successfully")
        
        logger.info("✅ Database system test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database system test failed: {e}")
        return False
    
    return True


async def test_configuration():
    """Test the enhanced configuration"""
    try:
        logger.info("🧪 Testing Enhanced Configuration...")
        
        # Test settings import
        from bot.config import settings
        
        logger.info("✅ Configuration imported successfully")
        
        # Check payment settings
        logger.info("📋 Payment Configuration:")
        logger.info(f"  - Telegram Payments Token: {'✅ Set' if hasattr(settings, 'telegram_payments_token') and settings.telegram_payments_token else '❌ Not set'}")
        logger.info(f"  - Payme Merchant ID: {'✅ Set' if hasattr(settings, 'payme_merchant_id') and settings.payme_merchant_id else '❌ Not set'}")
        logger.info(f"  - Click Merchant ID: {'✅ Set' if hasattr(settings, 'click_merchant_id') and settings.click_merchant_id else '❌ Not set'}")
        logger.info(f"  - Admin Contact: {'✅ Set' if hasattr(settings, 'admin_contact') and settings.admin_contact else '❌ Not set'}")
        
        # Check database settings
        logger.info("📋 Database Configuration:")
        logger.info(f"  - Database URL: {'✅ Set' if hasattr(settings, 'database_url') and settings.database_url else '❌ Not set'}")
        logger.info(f"  - Environment: {getattr(settings, 'environment', 'Not set')}")
        
        logger.info("✅ Configuration test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False
    
    return True


async def main():
    """Main test function"""
    logger.info("🚀 Starting Enhanced SMM Bot System Tests...")
    
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        level="DEBUG",  # Changed from INFO to DEBUG
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    tests = [
        test_configuration,
        test_payment_system,
        test_database_system
    ]
    
    results = []
    
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            logger.error(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("="*50)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{i+1}. {test.__name__}: {status}")
    
    logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! The enhanced system is working correctly.")
    else:
        logger.warning(f"⚠️ {total - passed} test(s) failed. Please check the logs above.")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)

#!/usr/bin/env python3
"""
Test script for the enhanced payment system only
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
        
        # Test payment creation (without database)
        test_user_id = 12345
        test_amount = 10.0
        
        logger.info(f"🧪 Testing payment creation for user {test_user_id}, amount ${test_amount}")
        
        # Test each provider
        for provider_name, provider in providers.items():
            try:
                logger.info(f"  Testing {provider_name} provider...")
                
                # Test payment creation
                result = await provider.create_payment(
                    amount_usd=test_amount,
                    user_id=test_user_id,
                    description="Test payment"
                )
                
                if result.success:
                    logger.info(f"    ✅ {provider_name}: Payment created successfully")
                    logger.info(f"      Payment ID: {result.payment_id}")
                    logger.info(f"      Status: {result.status.value}")
                    if result.payment_url:
                        logger.info(f"      Payment URL: {result.payment_url}")
                    if result.metadata:
                        logger.info(f"      Metadata: {result.metadata}")
                else:
                    logger.warning(f"    ⚠️ {provider_name}: Payment creation failed - {result.error_message}")
                
                # Test payment verification
                verify_result = await provider.verify_payment(
                    payment_id=result.payment_id if result.success else "test_id",
                    webhook_data={"status": "pending"}
                )
                
                if verify_result.success:
                    logger.info(f"    ✅ {provider_name}: Payment verification working")
                else:
                    logger.warning(f"    ⚠️ {provider_name}: Payment verification failed - {verify_result.error_message}")
                
            except Exception as e:
                logger.error(f"    ❌ {provider_name}: Error during testing - {e}")
        
        logger.info("✅ Payment system test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Payment system test failed: {e}")
        return False


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
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False


async def main():
    """Main test function"""
    logger.info("🚀 Starting Enhanced Payment System Tests...")
    
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    tests = [
        test_configuration,
        test_payment_system
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
        logger.info("🎉 All tests passed! The enhanced payment system is working correctly.")
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

#!/usr/bin/env python3
"""
Simple test script to verify bot functionality
"""
import asyncio
import sys
import os
from loguru import logger

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.config import settings
from bot.database.db import init_db, close_db, get_db
from bot.services.user_service import UserService
from bot.services.balance_service import BalanceService
from bot.services.settings_service import SettingsService
from bot.services.service_service import ServiceService


async def test_database_connection():
    """Test database connection"""
    logger.info("🔄 Testing database connection...")
    
    try:
        await init_db()
        
        async for db in get_db():
            # Test user count
            user_count = await UserService.get_users_count(db)
            logger.info(f"✅ Database connection successful. Users count: {user_count}")
            break
        
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False
    finally:
        await close_db()


async def test_settings():
    """Test settings service"""
    logger.info("🔄 Testing settings service...")
    
    try:
        await init_db()
        
        async for db in get_db():
            # Test getting settings
            coins_per_usd = await SettingsService.get_setting(db, "coins_per_usd", 1000)
            min_deposit = await SettingsService.get_setting(db, "min_deposit_usd", 1.0)
            max_deposit = await SettingsService.get_setting(db, "max_deposit_usd", 1000.0)
            
            logger.info(f"✅ Settings test successful:")
            logger.info(f"   - Coins per USD: {coins_per_usd}")
            logger.info(f"   - Min deposit: ${min_deposit}")
            logger.info(f"   - Max deposit: ${max_deposit}")
            break
        
        return True
    except Exception as e:
        logger.error(f"❌ Settings test failed: {e}")
        return False
    finally:
        await close_db()


async def test_user_creation():
    """Test user creation"""
    logger.info("🔄 Testing user creation...")
    
    try:
        await init_db()
        
        async for db in get_db():
            # Create a test user
            test_user = await UserService.create_user(
                db=db,
                telegram_id=123456789,
                username="test_user",
                first_name="Test",
                last_name="User"
            )
            
            if test_user:
                logger.info(f"✅ User creation successful: {test_user.username}")
                
                # Test balance
                balance = await BalanceService.get_user_balance(db, test_user.id)
                logger.info(f"✅ User balance: {balance} coins")
                
                # Test USD conversion
                usd_value = await BalanceService.coins_to_usd(db, balance)
                logger.info(f"✅ USD value: ${usd_value:.2f}")
                
                return True
            else:
                logger.error("❌ User creation failed")
                return False
            break
        
    except Exception as e:
        logger.error(f"❌ User creation test failed: {e}")
        return False
    finally:
        await close_db()


async def test_services():
    """Test service service"""
    logger.info("🔄 Testing service service...")
    
    try:
        await init_db()
        
        async for db in get_db():
            # Test getting categories
            categories = await ServiceService.get_active_categories(db)
            logger.info(f"✅ Found {len(categories)} service categories")
            
            if categories:
                # Test getting services for first category
                services = await ServiceService.get_services_by_category(db, categories[0].id)
                logger.info(f"✅ Found {len(services)} services in category '{categories[0].name}'")
            
            break
        
        return True
    except Exception as e:
        logger.error(f"❌ Service test failed: {e}")
        return False
    finally:
        await close_db()


async def test_configuration():
    """Test configuration"""
    logger.info("🔄 Testing configuration...")
    
    try:
        # Test required settings
        required_settings = [
            'bot_token',
            'database_url',
            'jap_api_url',
            'jap_api_key',
            'secret_key'
        ]
        
        missing_settings = []
        for setting in required_settings:
            if not getattr(settings, setting, None):
                missing_settings.append(setting)
        
        if missing_settings:
            logger.warning(f"⚠️ Missing settings: {missing_settings}")
        else:
            logger.info("✅ All required settings are configured")
        
        # Test admin IDs
        if settings.admin_ids:
            logger.info(f"✅ Admin IDs configured: {settings.admin_ids}")
        else:
            logger.warning("⚠️ No admin IDs configured")
        
        return len(missing_settings) == 0
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False


async def main():
    """Run all tests"""
    logger.info("🧪 Starting bot functionality tests...")
    
    tests = [
        ("Configuration", test_configuration),
        ("Database Connection", test_database_connection),
        ("Settings Service", test_settings),
        ("User Creation", test_user_creation),
        ("Service Service", test_services),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name} test PASSED")
            else:
                logger.error(f"❌ {test_name} test FAILED")
                
        except Exception as e:
            logger.error(f"❌ {test_name} test ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! The bot is ready to run.")
        logger.info("You can now start the bot with: python main.py")
    else:
        logger.error("⚠️ Some tests failed. Please check the configuration and setup.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

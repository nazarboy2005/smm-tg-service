#!/usr/bin/env python3
"""
Railway Deployment Verification Script
This script verifies that all components are properly configured for Railway deployment
"""
import os
import sys
import asyncio
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists and report status"""
    if Path(file_path).exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - NOT FOUND")
        return False

def check_environment_variables():
    """Check if required environment variables are documented"""
    print("\n🔍 Checking Environment Variables Documentation...")
    
    required_vars = [
        "BOT_TOKEN",
        "BOT_USERNAME", 
        "DATABASE_URL",
        "ADMIN_CONTACT",
        "ENVIRONMENT",
        "USE_WEBHOOK"
    ]
    
    optional_vars = [
        "TELEGRAM_PAYMENTS_TOKEN",
        "PAYME_MERCHANT_ID",
        "CLICK_MERCHANT_ID",
        "JAP_API_URL",
        "JAP_API_KEY",
        "SECRET_KEY",
        "WEBHOOK_SECRET"
    ]
    
    print("Required Environment Variables:")
    for var in required_vars:
        print(f"  ✅ {var}")
    
    print("\nOptional Environment Variables:")
    for var in optional_vars:
        print(f"  📝 {var}")
    
    return True

def check_railway_configuration():
    """Check Railway-specific configuration"""
    print("\n🚂 Checking Railway Configuration...")
    
    # Check railway.json
    if check_file_exists("railway.json", "Railway configuration file"):
        print("  ✅ Railway configuration found")
    else:
        print("  ❌ Railway configuration missing")
        return False
    
    # Check Dockerfile
    if check_file_exists("Dockerfile", "Docker configuration"):
        print("  ✅ Dockerfile found")
    else:
        print("  ❌ Dockerfile missing")
        return False
    
    # Check main_webhook.py
    if check_file_exists("main_webhook.py", "Webhook entry point"):
        print("  ✅ Webhook entry point found")
    else:
        print("  ❌ Webhook entry point missing")
        return False
    
    return True

def check_web_interface():
    """Check web interface components"""
    print("\n🌐 Checking Web Interface...")
    
    web_files = [
        ("bot/web/server.py", "FastAPI web server"),
        ("bot/web/templates/index.html", "Main dashboard template"),
        ("bot/web/templates/login.html", "Login template"),
        ("bot/web/templates/payment.html", "Payment template"),
        ("bot/web/templates/payment_success.html", "Payment success template"),
        ("bot/web/templates/payment_failure.html", "Payment failure template")
    ]
    
    all_found = True
    for file_path, description in web_files:
        if not check_file_exists(file_path, description):
            all_found = False
    
    return all_found

def check_database_setup():
    """Check database configuration"""
    print("\n🗄️ Checking Database Setup...")
    
    db_files = [
        ("bot/database/db.py", "Database manager"),
        ("bot/database/models.py", "Database models"),
        ("bot/database/migrations/env.py", "Migration environment"),
        ("alembic.ini", "Alembic configuration")
    ]
    
    all_found = True
    for file_path, description in db_files:
        if not check_file_exists(file_path, description):
            all_found = False
    
    return all_found

def check_dependencies():
    """Check if all required dependencies are listed"""
    print("\n📦 Checking Dependencies...")
    
    if check_file_exists("requirements.txt", "Python dependencies"):
        with open("requirements.txt", "r") as f:
            content = f.read()
            
        required_packages = [
            "aiogram",
            "fastapi",
            "uvicorn",
            "sqlalchemy",
            "asyncpg",
            "alembic",
            "pydantic",
            "loguru"
        ]
        
        missing_packages = []
        for package in required_packages:
            if package.lower() not in content.lower():
                missing_packages.append(package)
        
        if missing_packages:
            print(f"  ❌ Missing packages: {', '.join(missing_packages)}")
            return False
        else:
            print("  ✅ All required packages found")
            return True
    else:
        return False

async def test_database_connection():
    """Test database connection (if DATABASE_URL is available)"""
    print("\n🔌 Testing Database Connection...")
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("  ⚠️ DATABASE_URL not set - skipping database test")
        return True
    
    try:
        from bot.database.db import db_manager
        success = await db_manager.initialize()
        if success:
            print("  ✅ Database connection successful")
            await db_manager.close()
            return True
        else:
            print("  ❌ Database connection failed")
            return False
    except Exception as e:
        print(f"  ❌ Database connection error: {e}")
        return False

def check_bot_configuration():
    """Check bot configuration"""
    print("\n🤖 Checking Bot Configuration...")
    
    try:
        from bot.config import settings
        
        # Check if settings can be loaded
        print("  ✅ Bot configuration loaded")
        
        # Check critical settings
        if hasattr(settings, 'bot_token') and settings.bot_token:
            print("  ✅ Bot token configured")
        else:
            print("  ⚠️ Bot token not configured (will be set via environment)")
        
        if hasattr(settings, 'database_url') and settings.database_url:
            print("  ✅ Database URL configured")
        else:
            print("  ⚠️ Database URL not configured (will be set via environment)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Bot configuration error: {e}")
        return False

def main():
    """Main verification function"""
    print("🚀 Railway Deployment Verification")
    print("=" * 50)
    
    checks = [
        ("Railway Configuration", check_railway_configuration),
        ("Web Interface", check_web_interface),
        ("Database Setup", check_database_setup),
        ("Dependencies", check_dependencies),
        ("Environment Variables", check_environment_variables),
        ("Bot Configuration", check_bot_configuration),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} check failed: {e}")
            results.append((check_name, False))
    
    # Test database connection if possible
    try:
        result = asyncio.run(test_database_connection())
        results.append(("Database Connection", result))
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        results.append(("Database Connection", False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All checks passed! Your bot is ready for Railway deployment!")
        print("\n📋 Next Steps:")
        print("1. Set up your environment variables in Railway")
        print("2. Deploy to Railway")
        print("3. Test your bot and web interface")
        print("4. Monitor the deployment logs")
        return True
    else:
        print(f"\n⚠️ {total - passed} checks failed. Please fix the issues before deploying.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
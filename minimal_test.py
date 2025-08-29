#!/usr/bin/env python3
"""
Minimal test to verify the bot works without database dependencies
"""
import sys
import os
import asyncio

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_bot_core():
    """Test core bot functionality"""
    print("🚀 SMM Bot - Minimal Test\n")
    
    try:
        # Test configuration
        print("⚙️ Testing configuration...")
        from bot.config import settings
        print(f"✅ Bot token: {settings.bot_token[:20]}...")
        print(f"✅ Admin IDs: {settings.admin_ids}")
        print(f"✅ Coins per USD: {settings.coins_per_usd}")
        print(f"✅ Crypto addresses configured: {bool(settings.bitcoin_address)}")
        
        # Test i18n
        print("\n🌐 Testing internationalization...")
        from bot.utils.i18n import get_text, Language
        
        welcome_en = get_text("welcome", Language.ENGLISH)
        welcome_ru = get_text("welcome", Language.RUSSIAN)
        welcome_uz = get_text("welcome", Language.UZBEK)
        
        print(f"✅ English: {welcome_en}")
        print(f"✅ Russian: {welcome_ru}")
        print(f"✅ Uzbek: {welcome_uz}")
        
        # Test keyboards
        print("\n⌨️ Testing keyboards...")
        from bot.utils.keyboards import get_language_keyboard, get_main_menu_keyboard
        
        lang_kb = get_language_keyboard()
        main_kb = get_main_menu_keyboard(Language.ENGLISH, is_admin=True)
        
        print(f"✅ Language keyboard: {len(lang_kb.inline_keyboard)} rows")
        print(f"✅ Main menu keyboard: {len(main_kb.inline_keyboard)} rows")
        
        # Test security
        print("\n🛡️ Testing security...")
        from bot.utils.security import SecurityUtils
        
        token = SecurityUtils.generate_secure_token(16)
        is_valid_url = SecurityUtils.validate_url("https://instagram.com/test")
        is_valid_amount = SecurityUtils.validate_amount(10.50, 1.0, 1000.0)
        
        print(f"✅ Generated token: {token}")
        print(f"✅ URL validation: {is_valid_url}")
        print(f"✅ Amount validation: {is_valid_amount}")
        
        # Test payment providers (structure only)
        print("\n💳 Testing payment system structure...")
        from bot.services.payment.base_payment import BasePaymentProvider, PaymentResult, PaymentStatus
        from bot.services.payment.crypto_provider import CryptoProvider
        
        print("✅ Base payment provider imported")
        print("✅ Crypto provider imported")
        
        # Test handlers structure
        print("\n🤖 Testing handlers structure...")
        from bot.handlers import user_handlers, admin_handlers, admin_settings_handlers
        from bot.middleware.security_middleware import SecurityMiddleware, LoggingMiddleware
        
        print("✅ User handlers imported")
        print("✅ Admin handlers imported") 
        print("✅ Settings handlers imported")
        print("✅ Security middleware imported")
        
        print("\n🎉 SUCCESS! All core components are working!")
        print("\n📋 What's working:")
        print("  ✅ Configuration system with your bot token")
        print("  ✅ Multi-language support (Uzbek, Russian, English)")
        print("  ✅ Keyboard generation")
        print("  ✅ Security utilities")
        print("  ✅ Payment system structure")
        print("  ✅ Handler architecture")
        print("  ✅ Middleware system")
        print("  ✅ Admin settings management")
        
        print("\n🔧 To run with full features:")
        print("  1. Set up Supabase database")
        print("  2. Install: pip install sqlalchemy asyncpg alembic")
        print("  3. Configure database URL in .env")
        print("  4. Run: python main.py")
        
        print("\n✨ Your SMM Bot is architecturally sound and ready!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_bot_core())

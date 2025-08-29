#!/usr/bin/env python3
"""
Test bot structure and imports
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all modules can be imported"""
    print("🧪 Testing bot structure...")
    
    try:
        # Test config
        from bot.config import settings
        print("✅ Config loaded")
        
        # Test i18n
        from bot.utils.i18n import get_text, Language
        text = get_text("welcome", Language.ENGLISH)
        print(f"✅ i18n working: '{text[:30]}...'")
        
        # Test keyboards
        from bot.utils.keyboards import get_language_keyboard
        keyboard = get_language_keyboard()
        print("✅ Keyboards working")
        
        # Test security
        from bot.utils.security import SecurityUtils
        token = SecurityUtils.generate_secure_token()
        print(f"✅ Security utils working: token length {len(token)}")
        
        # Test handlers
        from bot.handlers import user_handlers, admin_handlers, admin_settings_handlers
        print("✅ Handlers imported")
        
        # Test middleware
        from bot.middleware.security_middleware import SecurityMiddleware
        print("✅ Middleware imported")
        
        print("\n🎉 All core modules imported successfully!")
        print("📋 Bot structure is valid and ready for development")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_configuration():
    """Test configuration"""
    print("\n⚙️ Testing configuration...")
    
    try:
        from bot.config import settings
        
        print(f"Bot token configured: {'Yes' if settings.bot_token else 'No'}")
        print(f"Admin IDs: {len(settings.admin_ids)} configured")
        print(f"Environment: {settings.environment}")
        print(f"Log level: {settings.log_level}")
        
        # Test crypto addresses
        print(f"Bitcoin address: {settings.bitcoin_address[:10]}..." if settings.bitcoin_address else "Bitcoin address: Not set")
        
        print("✅ Configuration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 SMM Bot Structure Test\n")
    
    # Test imports
    if not test_imports():
        sys.exit(1)
    
    # Test configuration  
    if not test_configuration():
        sys.exit(1)
    
    print("\n✅ All tests passed!")
    print("\n📋 Next steps:")
    print("1. Set up Supabase database")
    print("2. Configure .env file with your credentials")
    print("3. Install full dependencies: pip install -r requirements.txt")
    print("4. Run: python main.py")
    
    print("\n🌟 Your SMM Bot is ready for development!")


if __name__ == "__main__":
    main()

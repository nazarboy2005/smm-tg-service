#!/usr/bin/env python3
"""
Simple startup script for the SMM Bot in polling mode
"""
import os
import sys
from loguru import logger

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main startup function"""
    try:
        logger.info("🚀 Starting SMM Bot in polling mode...")
        
        # Check if .env file exists
        if not os.path.exists('.env'):
            logger.warning("⚠️ No .env file found. Please create one based on env.example")
            logger.info("💡 Copy env.example to .env and configure your settings")
            return
        
        # Import and run the main bot
        from main import main as bot_main
        import asyncio
        
        logger.info("✅ Configuration loaded successfully")
        logger.info("🤖 Starting bot in polling mode...")
        logger.info("📱 Bot will listen for messages and respond")
        logger.info("🛑 Press Ctrl+C to stop the bot")
        
        # Run the bot
        asyncio.run(bot_main())
        
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
        logger.info("💡 Make sure you have:")
        logger.info("   1. Created a .env file with your configuration")
        logger.info("   2. Set your BOT_TOKEN in the .env file")
        logger.info("   3. Installed all dependencies: pip install -r requirements.txt")
        sys.exit(1)

if __name__ == "__main__":
    main()

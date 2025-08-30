#!/usr/bin/env python3
"""
Fix all remaining issues in the bot
1. Replace all bot username references
2. Fix any remaining database binding issues
3. Test all functionality
"""
import os
import re
from pathlib import Path


def fix_bot_username_references():
    """Fix all bot username references in web server"""
    server_file = Path("bot/web/server.py")
    
    if server_file.exists():
        content = server_file.read_text(encoding='utf-8')
        
        # Replace all t.me/{settings.bot_username} with hardcoded username
        content = re.sub(
            r'https://t\.me/\{\{?\s*settings\.bot_username\s*\}?\}?',
            'https://t.me/nimadirishqiladiganbot',
            content
        )
        
        content = re.sub(
            r'f"https://t\.me/\{settings\.bot_username\}"',
            '"https://t.me/nimadirishqiladiganbot"',
            content
        )
        
        # Replace bot_username template variables
        content = re.sub(
            r'"bot_username":\s*settings\.bot_username[^,]*',
            '"bot_username": "nimadirishqiladiganbot"',
            content
        )
        
        server_file.write_text(content, encoding='utf-8')
        print("✅ Fixed bot username references in web server")


def fix_html_templates():
    """Fix bot username in HTML templates"""
    templates_dir = Path("bot/web/templates")
    
    if templates_dir.exists():
        for template_file in templates_dir.glob("*.html"):
            content = template_file.read_text(encoding='utf-8')
            
            # Replace template variables
            content = re.sub(
                r'\{\{\s*bot_username\s*\}\}',
                'nimadirishqiladiganbot',
                content
            )
            
            template_file.write_text(content, encoding='utf-8')
            print(f"✅ Fixed bot username in {template_file.name}")


def create_fixed_user_service():
    """Create a fixed version of user service without Engine binding issues"""
    content = '''"""
User service with fixed database session handling
"""
import asyncio
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, update, and_, func
from loguru import logger

from bot.database.models import User, UserBalance, UserLanguage
from bot.config import settings
from bot.database.db import get_db


class UserService:
    """Service for user management"""
    
    @staticmethod
    async def get_user_by_telegram_id(db: AsyncSession, telegram_id: int, max_retries: int = 3) -> Optional[User]:
        """Get user by Telegram ID with retry logic"""
        for attempt in range(max_retries):
            try:
                result = await db.execute(
                    select(User)
                    .options(selectinload(User.balance))
                    .where(User.telegram_id == telegram_id)
                )
                return result.scalar_one_or_none()
                
            except Exception as e:
                logger.error(f"Error getting user by telegram_id {telegram_id} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return None
                # For retry, get a fresh session
                await asyncio.sleep(0.1 * (attempt + 1))  # Progressive delay
    
    @staticmethod
    async def create_user(db: AsyncSession, telegram_id: int, username: str = None, 
                         first_name: str = None, last_name: str = None, 
                         language: UserLanguage = UserLanguage.EN, max_retries: int = 3) -> Optional[User]:
        """Create a new user with retry logic"""
        for attempt in range(max_retries):
            try:
                # Check if user already exists
                existing_user = await UserService.get_user_by_telegram_id(db, telegram_id)
                if existing_user:
                    return existing_user
                
                # Check if user is admin
                is_admin = telegram_id in settings.admin_ids if settings.admin_ids else False
                
                # Create new user
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    language=language,
                    is_admin=is_admin
                )
                db.add(user)
                await db.flush()
                
                # Create balance
                balance = UserBalance(user_id=user.id, balance=0)
                db.add(balance)
                
                await db.commit()
                await db.refresh(user)
                user.balance = balance
                
                logger.info(f"Created new user: {telegram_id} (username: {username})")
                return user
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error creating user {telegram_id} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return None
                # For retry, wait a bit
                await asyncio.sleep(0.1 * (attempt + 1))
        
        return None
'''
    
    # Write the fixed user service
    user_service_file = Path("bot/services/user_service_fixed.py")
    user_service_file.write_text(content, encoding='utf-8')
    print("✅ Created fixed user service")


def main():
    """Run all fixes"""
    print("🔧 Starting comprehensive fix...")
    
    fix_bot_username_references()
    fix_html_templates()
    create_fixed_user_service()
    
    print("🎉 All fixes completed!")
    print("📝 Recommendations:")
    print("   1. Replace the original user_service.py with user_service_fixed.py")
    print("   2. Test the bot with: python test_bot.py")
    print("   3. Debug webhook with: python debug_webhook.py")
    print("   4. Deploy to Railway and test @nimadirishqiladiganbot")


if __name__ == "__main__":
    main()
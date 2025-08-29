#!/usr/bin/env python3
"""
Create initial database migration
"""
import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alembic.config import Config
from alembic import command


def create_initial_migration():
    """Create initial migration"""
    try:
        # Configure Alembic
        alembic_cfg = Config("alembic.ini")
        
        # Create initial migration
        command.revision(
            alembic_cfg,
            message="Initial migration",
            autogenerate=True
        )
        
        print("✅ Initial migration created successfully!")
        print("Run 'alembic upgrade head' to apply the migration.")
        
    except Exception as e:
        print(f"❌ Error creating migration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    create_initial_migration()

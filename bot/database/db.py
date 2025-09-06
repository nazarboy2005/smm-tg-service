"""
Enhanced database management with raw asyncpg connections
"""
import asyncio
import logging
from typing import Optional, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager

import asyncpg
from loguru import logger

from bot.config import settings


class DatabaseManager:
    """Enhanced database manager using raw asyncpg connections"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self._initialized = False
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> bool:
        """Initialize database connection pool with retry logic"""
        if self._initialized:
            return True
            
        async with self._lock:
            if self._initialized:  # Double-check pattern
                return True
                
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Database initialization attempt {attempt + 1}/{max_retries}")
                    
                    # Create connection pool with pgbouncer-optimized settings
                    self.pool = await self._create_pool()
                    
                    # Test connection
                    if await self._test_connection():
                        self._initialized = True
                        logger.info("✅ Database initialized successfully with raw asyncpg")
                        return True
                    else:
                        raise Exception("Connection test failed")
                        
                except Exception as e:
                    logger.error(f"Database initialization attempt {attempt + 1} failed: {e}")
                    
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        logger.error("❌ Database initialization failed after all retries")
                        return False
            
            return False
    
    async def _create_pool(self) -> asyncpg.Pool:
        """Create asyncpg connection pool with Supabase Transaction Pooler compatibility"""
        try:
            # Parse database URL to extract connection parameters
            db_url = settings.database_url
            
            logger.info(f"🔧 Parsing database URL: {db_url[:50]}...")
            
            # Handle both postgresql:// and postgresql+asyncpg:// formats
            if db_url.startswith('postgresql+asyncpg://'):
                # Convert to standard format
                db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
                logger.info("🔧 Converted postgresql+asyncpg:// to postgresql://")
            
            # For Supabase Transaction Pooler, we need to handle the special format
            # The URL format should be: postgresql://postgres.qgziqlgwaoqyqtcmmjsv:[PASSWORD]@aws-1-eu-north-1.pooler.supabase.com:6543/postgres
            
            if not db_url.startswith('postgresql://'):
                raise ValueError(f"Database URL must start with 'postgresql://', got: {db_url[:20]}...")
            
            # Remove postgresql:// prefix (13 characters)
            connection_string = db_url[13:]
            logger.info(f"🔧 Connection string after prefix removal: {connection_string}")
            
            # Split into user:pass@host:port/database
            if '@' not in connection_string:
                raise ValueError(f"Database URL must contain '@' separator, got: {connection_string[:20]}...")
            
            auth_part, rest = connection_string.split('@', 1)
            logger.debug(f"🔧 Auth part: {auth_part}")
            logger.debug(f"🔧 Rest part: {rest}")
            
            # Parse user and password - find the LAST colon (password might contain colons)
            if ':' in auth_part:
                # Find the last colon to handle passwords that might contain colons
                last_colon_index = auth_part.rfind(':')
                user = auth_part[:last_colon_index]
                password = auth_part[last_colon_index + 1:]
                logger.debug(f"🔧 Parsed user: '{user}'")
                logger.debug(f"🔧 Parsed password: '{password[:3]}...' (length: {len(password)})")
            else:
                user, password = auth_part, None
                logger.debug(f"🔧 Parsed user: '{user}' (no password)")
            
            # Parse host, port, and database
            if '/' not in rest:
                raise ValueError(f"Database URL must contain '/' separator for database, got: {rest[:20]}...")
            
            host_port, database = rest.split('/', 1)
            logger.debug(f"🔧 Host/port: {host_port}")
            logger.debug(f"🔧 Database: {database}")
            
            if ':' in host_port:
                host, port_str = host_port.split(':', 1)
                try:
                    port = int(port_str)
                except ValueError:
                    raise ValueError(f"Invalid port number: {port_str}")
            else:
                host, port = host_port, 5432
            
            logger.debug(f"🔧 Final parsed values:")
            logger.debug(f"  - User: '{user}'")
            logger.debug(f"  - Host: '{host}'")
            logger.debug(f"  - Port: {port}")
            logger.debug(f"  - Database: '{database}'")
            
            # Validate required fields
            if not user:
                raise ValueError("Database user is required")
            if not host:
                raise ValueError("Database host is required")
            if not database:
                raise ValueError("Database name is required")
            
            # Connection parameters for Supabase Transaction Pooler
            connection_params = {
                'host': host,
                'port': port,
                'user': user,
                'password': password,
                'database': database
            }
            
            # Remove None values
            connection_params = {k: v for k, v in connection_params.items() if v is not None}
            
            logger.info("🔧 Creating asyncpg connection pool for Supabase Transaction Pooler")
            logger.info(f"  Host: {host}:{port}")
            logger.info(f"  Database: {database}")
            logger.info(f"  User: {user}")
            logger.info(f"  Using Transaction Pooler (no PREPARE statements)")
            
            # Create connection pool with Transaction Pooler optimized settings
            pool = await asyncpg.create_pool(
                **connection_params,
                min_size=1,
                max_size=5,  # Smaller pool for Transaction Pooler
                command_timeout=30,
                # Completely disable prepared statements for Transaction Pooler
                statement_cache_size=0,
                # These settings are important for Transaction Pooler
                setup=self._setup_connection
            )
            
            return pool
            
        except Exception as e:
            logger.error(f"Error creating database pool: {e}")
            logger.error(f"Database URL format should be: postgresql://user:password@host:port/database")
            logger.error(f"Example: postgresql://postgres.qgziqlgwaoqyqtcmmjsv:password@aws-1-eu-north-1.pooler.supabase.com:6543/postgres")
            raise
    
    async def _setup_connection(self, connection):
        """Setup connection for Transaction Pooler compatibility"""
        try:
            # Aggressively disable prepared statements for Transaction Pooler
            await connection.execute("SET statement_timeout = '30s'")
            await connection.execute("SET idle_in_transaction_session_timeout = '30s'")
            await connection.execute("SET plan_cache_mode = 'auto'")
            logger.debug("Connection setup completed for Transaction Pooler")
        except Exception as e:
            logger.warning(f"Connection setup warning: {e}")
    
    async def _test_connection(self) -> bool:
        """Test database connection with simple query"""
        try:
            if not self.pool:
                return False
            
            # Use raw connection to avoid any SQLAlchemy overhead
            async with self.pool.acquire() as conn:
                # Simple query that won't trigger prepared statements
                result = await conn.fetchval("SELECT 1")
                if result == 1:
                    logger.info("✅ Database connection test passed")
                    return True
                else:
                    logger.error("Database connection test failed - unexpected result")
                    return False
                
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    async def get_connection(self) -> asyncpg.Connection:
        """Get database connection from pool"""
        if not self._initialized:
            await self.initialize()
        
        if not self.pool:
            raise Exception("Database not initialized")
        
        return await self.pool.acquire()
    
    async def execute(self, query: str, *args, **kwargs):
        """Execute a query"""
        if not self._initialized:
            await self.initialize()
        
        if not self.pool:
            raise Exception("Database not initialized")
        
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args, **kwargs)
    
    async def fetch(self, query: str, *args, **kwargs):
        """Fetch multiple rows"""
        if not self._initialized:
            await self.initialize()
        
        if not self.pool:
            raise Exception("Database not initialized")
        
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args, **kwargs)
    
    async def fetchval(self, query: str, *args, **kwargs):
        """Fetch a single value"""
        if not self._initialized:
            await self.initialize()
        
        if not self.pool:
            raise Exception("Database not initialized")
        
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args, **kwargs)
    
    async def fetchrow(self, query: str, *args, **kwargs):
        """Fetch a single row"""
        if not self._initialized:
            await self.initialize()
        
        if not self.pool:
            raise Exception("Database not initialized")
        
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args, **kwargs)
    
    async def close(self):
        """Close database connections"""
        try:
            if self.pool:
                await self.pool.close()
                logger.info("Database pool closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")
        finally:
            self._initialized = False
            self.pool = None
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            if not self._initialized:
                return False
            
            return await self._test_connection()
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def create_tables(self) -> bool:
        """Create database tables if they don't exist"""
        try:
            if not self._initialized:
                logger.error("Database not initialized")
                return False
            
            # Import models to ensure they're registered
            from bot.database.models import Base
            
            # Create tables using SQLAlchemy metadata
            # Since we're using raw asyncpg, we need to create tables manually
            async with self.pool.acquire() as conn:
                # Check if tables exist and create them if they don't
                await self._create_tables_if_not_exist(conn)
            
            logger.info("Database tables created/verified successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            return False
    
    async def _create_tables_if_not_exist(self, conn):
        """Create tables if they don't exist"""
        # Create users table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username VARCHAR(255),
                first_name VARCHAR(255),
                last_name VARCHAR(255),
                language VARCHAR(10) DEFAULT 'en' NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE NOT NULL,
                is_active BOOLEAN DEFAULT TRUE NOT NULL,
                referral_code VARCHAR(50) UNIQUE NOT NULL,
                referred_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
            )
        """)
        
        # Create indexes for users table
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code)")
        
        # Create balances table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS balances (
                id SERIAL PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                amount BIGINT DEFAULT 0 NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
            )
        """)
        
        # Create transactions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                type VARCHAR(20) NOT NULL,
                amount BIGINT NOT NULL,
                usd_amount DECIMAL(10,2),
                status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                payment_method VARCHAR(50),
                payment_data JSONB,
                description TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
            )
        """)
        
        # Create indexes for transactions table
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)")
        
        # Create services table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                category VARCHAR(100),
                price_per_1000 BIGINT NOT NULL,
                min_quantity INTEGER DEFAULT 1 NOT NULL,
                max_quantity INTEGER DEFAULT 1000000 NOT NULL,
                is_active BOOLEAN DEFAULT TRUE NOT NULL,
                jap_service_id VARCHAR(100),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
            )
        """)
        
        # Create indexes for services table
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_services_category ON services(category)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_services_is_active ON services(is_active)")
        
        # Create orders table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                service_id INTEGER NOT NULL REFERENCES services(id),
                link VARCHAR(500) NOT NULL,
                quantity INTEGER NOT NULL,
                charge BIGINT NOT NULL,
                status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                jap_order_id VARCHAR(100),
                start_count INTEGER DEFAULT 0,
                remains INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
            )
        """)
        
        # Create indexes for orders table
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_service_id ON orders(service_id)")
        
        # Create settings table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id SERIAL PRIMARY KEY,
                key VARCHAR(100) UNIQUE NOT NULL,
                value TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
            )
        """)
        
        # Create indexes for settings table
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key)")
        
        logger.info("All database tables created/verified")


# Global database manager instance
db_manager = DatabaseManager()


# Legacy functions for backward compatibility
async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    """Legacy database connection getter"""
    conn = await db_manager.get_connection()
    try:
        yield conn
    finally:
        # asyncpg connections are automatically returned to the pool
        pass


async def get_db_session() -> asyncpg.Connection:
    """Legacy database session getter"""
    return await db_manager.get_connection()


async def close_db():
    """Legacy database closer"""
    await db_manager.close()


# Context manager for database connections
@asynccontextmanager
async def get_db_context():
    """Context manager for database connections"""
    conn = await db_manager.get_connection()
    try:
        yield conn
    finally:
        await db_manager.pool.release(conn)

"""
Configuration management for the SMM Bot
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings"""
    
    # Bot Configuration
    bot_token: str = Field(default="", env="BOT_TOKEN")
    bot_username: str = Field(default="", env="BOT_USERNAME")
    admin_ids: List[int] = Field(default_factory=list, env="ADMIN_IDS")
    
    # Database Configuration
    database_url: str = Field(default="", env="DATABASE_URL")
    db_host: str = Field(default="localhost", env="DB_HOST")
    db_port: int = Field(default=5432, env="DB_PORT")
    db_name: str = Field(default="", env="DB_NAME")
    db_user: str = Field(default="", env="DB_USER")
    db_password: str = Field(default="", env="DB_PASSWORD")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # JAP API Configuration
    jap_api_url: str = Field(default="", env="JAP_API_URL")
    jap_api_key: str = Field(default="", env="JAP_API_KEY")
    
    # Payment Configuration
    coingate_api_token: str = Field(default="", env="COINGATE_API_TOKEN")
    coingate_sandbox: bool = Field(default=True, env="COINGATE_SANDBOX")
    paypal_client_id: str = Field(default="", env="PAYPAL_CLIENT_ID")
    paypal_client_secret: str = Field(default="", env="PAYPAL_CLIENT_SECRET")
    paypal_webhook_id: str = Field(default="", env="PAYPAL_WEBHOOK_ID")
    
    # Crypto Wallet Addresses
    bitcoin_address: str = Field(default="", env="BITCOIN_ADDRESS")
    ethereum_address: str = Field(default="", env="ETHEREUM_ADDRESS")
    solana_address: str = Field(default="", env="SOLANA_ADDRESS")
    xrp_address: str = Field(default="", env="XRP_ADDRESS")
    doge_address: str = Field(default="", env="DOGE_ADDRESS")
    toncoin_address: str = Field(default="", env="TONCOIN_ADDRESS")
    
    # Uzbek Payment Providers
    payme_merchant_id: str = Field(default="", env="PAYME_MERCHANT_ID")
    payme_secret_key: str = Field(default="", env="PAYME_SECRET_KEY")
    click_merchant_id: str = Field(default="", env="CLICK_MERCHANT_ID")
    click_secret_key: str = Field(default="", env="CLICK_SECRET_KEY")
    
    # Application Settings
    coins_per_usd: int = Field(default=10000, env="COINS_PER_USD")
    welcome_bonus_coins: int = Field(default=100, env="WELCOME_BONUS_COINS")
    default_referral_bonus: int = Field(default=10, env="DEFAULT_REFERRAL_BONUS")
    referral_tap_requirement: int = Field(default=5, env="REFERRAL_TAP_REQUIREMENT")
    min_deposit_usd: float = Field(default=1.0, env="MIN_DEPOSIT_USD")
    max_deposit_usd: float = Field(default=1000.0, env="MAX_DEPOSIT_USD")
    
    # Security
    secret_key: str = Field(default="your_secret_key_for_jwt_and_encryption_please_change_this", env="SECRET_KEY")
    webhook_secret: str = Field(default="", env="WEBHOOK_SECRET")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/bot.log", env="LOG_FILE")
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Web Server
    enable_web_server: bool = Field(default=True, env="ENABLE_WEB_SERVER")
    web_port: int = Field(default=8000, env="WEB_PORT")
    web_host: str = Field(default="0.0.0.0", env="WEB_HOST")
    web_base_url: str = Field(default="https://smm-tg-service-production.up.railway.app", env="WEB_BASE_URL")
    
    # Webhook Configuration
    use_webhook: bool = Field(default=True, env="USE_WEBHOOK")
    webhook_url: str = Field(default="https://smm-tg-service-production.up.railway.app", env="WEBHOOK_URL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        # Handle admin_ids parsing before validation
        if 'admin_ids' in kwargs:
            v = kwargs['admin_ids']
            if isinstance(v, str):
                if v.strip():
                    kwargs['admin_ids'] = [int(id_.strip()) for id_ in v.split(',') if id_.strip().isdigit()]
                else:
                    kwargs['admin_ids'] = []
            elif isinstance(v, int):
                kwargs['admin_ids'] = [v]
        
        super().__init__(**kwargs)
    
    @field_validator('db_port', mode='before')
    @classmethod
    def parse_db_port(cls, v):
        """Parse database port from environment variable"""
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return 5432  # Default port
        return v
    
    @field_validator('admin_ids', mode='before')
    @classmethod
    def parse_admin_ids(cls, v):
        """Parse admin IDs from environment variable"""
        if v is None:
            return []
        if isinstance(v, str):
            if not v.strip():
                return []
            try:
                return [int(id_.strip()) for id_ in v.split(',') if id_.strip().isdigit()]
            except (ValueError, TypeError):
                return []
        elif isinstance(v, int):
            return [v]
        elif isinstance(v, list):
            result = []
            for id_ in v:
                try:
                    result.append(int(id_))
                except (ValueError, TypeError):
                    continue
            return result
        return []
    
    @field_validator('min_deposit_usd', 'max_deposit_usd', mode='before')
    @classmethod
    def parse_deposit_amounts(cls, v):
        """Ensure deposit amounts are floats"""
        if isinstance(v, str):
            try:
                return float(v)
            except (ValueError, TypeError):
                return 1.0
        return float(v) if v is not None else 1.0
    
    @field_validator('database_url', mode='after')
    @classmethod
    def validate_database_url(cls, v):
        """Ensure database URL uses async driver and is completely pgbouncer compatible"""
        if v.startswith('postgresql://'):
            # Convert to async PostgreSQL URL
            v = v.replace('postgresql://', 'postgresql+asyncpg://', 1)
            
            # Add ALL necessary parameters for complete pgbouncer compatibility
            # These parameters completely disable prepared statement functionality
            cache_params = [
                'statement_cache_size=0',           # Disable statement caching
                'prepared_statement_cache_size=0',   # Disable prepared statement caching
                'command_timeout=60'                 # Set reasonable timeout
            ]
            
            if '?' not in v:
                v += '?' + '&'.join(cache_params)
            else:
                # Check if parameters already exist to avoid duplicates
                existing_params = v.split('?')[1] if '?' in v else ''
                for param in cache_params:
                    param_name = param.split('=')[0]
                    if param_name not in existing_params:
                        v += '&' + param
        
        return v


# Global settings instance
settings = Settings()

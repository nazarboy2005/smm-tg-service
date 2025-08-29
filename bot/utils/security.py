"""
Security utilities for the bot
"""
import hashlib
import hmac
import secrets
import string
from typing import Optional, Dict, Any
from loguru import logger
import re


class SecurityUtils:
    """Security utilities class"""
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate secure random token"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Use PBKDF2 for password hashing
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        
        return password_hash.hex(), salt
    
    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash"""
        new_hash, _ = SecurityUtils.hash_password(password, salt)
        return hmac.compare_digest(new_hash, password_hash)
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 1000) -> str:
        """Sanitize user input"""
        if not text:
            return ""
        
        # Remove null bytes and control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length]
        
        # Strip whitespace
        text = text.strip()
        
        return text
    
    @staticmethod
    def validate_telegram_id(telegram_id: int) -> bool:
        """Validate Telegram user ID"""
        # Telegram user IDs are positive integers
        # They're usually between 1 and 2^32
        try:
            # Convert to int if it's a string
            if isinstance(telegram_id, str):
                telegram_id = int(telegram_id)
            return isinstance(telegram_id, int) and 1 <= telegram_id <= 2**32
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return bool(url_pattern.match(url))
    
    @staticmethod
    def validate_amount(amount: float, min_amount: float = 0.01, max_amount: float = 10000.0) -> bool:
        """Validate monetary amount"""
        try:
            amount = float(amount)
            return min_amount <= amount <= max_amount
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_quantity(quantity: int, min_qty: int = 1, max_qty: int = 1000000) -> bool:
        """Validate order quantity"""
        try:
            quantity = int(quantity)
            return min_qty <= quantity <= max_qty
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def generate_webhook_signature(payload: bytes, secret: str) -> str:
        """Generate webhook signature"""
        return hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
    
    @staticmethod
    def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
        """Verify webhook signature"""
        expected_signature = SecurityUtils.generate_webhook_signature(payload, secret)
        return hmac.compare_digest(signature, expected_signature)
    
    @staticmethod
    def rate_limit_key(user_id: int, action: str) -> str:
        """Generate rate limit key"""
        return f"rate_limit:{user_id}:{action}"
    
    @staticmethod
    def log_security_event(
        event_type: str,
        user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "INFO"
    ):
        """Log security event"""
        log_data = {
            "event_type": event_type,
            "user_id": user_id,
            "details": details or {},
            "severity": severity
        }
        
        if severity == "CRITICAL":
            logger.critical(f"Security Event: {log_data}")
        elif severity == "ERROR":
            logger.error(f"Security Event: {log_data}")
        elif severity == "WARNING":
            logger.warning(f"Security Event: {log_data}")
        else:
            logger.info(f"Security Event: {log_data}")


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self._requests = {}
    
    def is_allowed(
        self,
        key: str,
        max_requests: int = 10,
        window_seconds: int = 60
    ) -> bool:
        """Check if request is allowed under rate limit"""
        import time
        
        now = time.time()
        window_start = now - window_seconds
        
        # Clean old requests
        if key in self._requests:
            self._requests[key] = [
                timestamp for timestamp in self._requests[key]
                if timestamp > window_start
            ]
        else:
            self._requests[key] = []
        
        # Check rate limit
        if len(self._requests[key]) >= max_requests:
            SecurityUtils.log_security_event(
                "rate_limit_exceeded",
                details={"key": key, "max_requests": max_requests, "window": window_seconds},
                severity="WARNING"
            )
            return False
        
        # Add current request
        self._requests[key].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()

"""
Base payment provider interface
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from enum import Enum


class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentResult:
    """Payment processing result"""
    
    def __init__(
        self,
        success: bool,
        payment_id: Optional[str] = None,
        payment_url: Optional[str] = None,
        status: PaymentStatus = PaymentStatus.PENDING,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.payment_id = payment_id
        self.payment_url = payment_url
        self.status = status
        self.error_message = error_message
        self.metadata = metadata or {}


class BasePaymentProvider(ABC):
    """Base payment provider interface"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_sandbox = config.get("sandbox", True)
    
    @abstractmethod
    async def create_payment(
        self,
        amount_usd: float,
        user_id: int,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentResult:
        """Create payment"""
        pass
    
    @abstractmethod
    async def verify_payment(
        self,
        payment_id: str,
        webhook_data: Optional[Dict[str, Any]] = None
    ) -> PaymentResult:
        """Verify payment status"""
        pass
    
    @abstractmethod
    async def cancel_payment(self, payment_id: str) -> bool:
        """Cancel payment"""
        pass
    
    @abstractmethod
    def validate_webhook(
        self,
        webhook_data: Dict[str, Any],
        signature: Optional[str] = None
    ) -> bool:
        """Validate webhook signature"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider name"""
        pass
    
    def format_amount(self, amount_usd: float) -> int:
        """Format amount for provider (usually in cents)"""
        return int(amount_usd * 100)
    
    def parse_amount(self, amount_cents: int) -> float:
        """Parse amount from provider (usually from cents)"""
        return amount_cents / 100

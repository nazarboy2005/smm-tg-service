"""
Simplified Uzbek payment providers - Focused on reliability
"""
import time
from typing import Optional, Dict, Any
from loguru import logger

from bot.services.payment.base_payment import BasePaymentProvider, PaymentResult, PaymentStatus


class SimplePaymeProvider(BasePaymentProvider):
    """Simplified Payme payment provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.merchant_id = config.get("merchant_id", "test_merchant")
        self.secret_key = config.get("secret_key", "test_secret")
        self.base_url = "https://checkout.test.paycom.uz" if self.is_sandbox else "https://checkout.paycom.uz"
    
    async def create_payment(
        self,
        amount_usd: float,
        user_id: int,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentResult:
        """Create simple Payme payment"""
        try:
            # Convert USD to UZS (approximate rate)
            amount_uzs = int(amount_usd * 12000)  # Amount in UZS
            
            # Create simple payment URL
            payment_url = (
                f"{self.base_url}/{self.merchant_id}?"
                f"ac.order_id={user_id}_{int(time.time())}&"
                f"a={amount_uzs}&"
                f"c={description or 'SMM Bot balance top-up'}"
            )
            
            payment_id = f"payme_{user_id}_{int(time.time())}"
            
            logger.info(f"Created Payme payment: {payment_id} for user {user_id}")
            
            return PaymentResult(
                success=True,
                payment_id=payment_id,
                payment_url=payment_url,
                status=PaymentStatus.PENDING,
                metadata={
                    "amount_uzs": amount_uzs,
                    "amount_usd": amount_usd,
                    "provider": "payme"
                }
            )
            
        except Exception as e:
            logger.error(f"Payme payment creation error: {e}")
            return PaymentResult(
                success=False,
                error_message="Payment creation failed"
            )
    
    async def verify_payment(
        self,
        payment_id: str,
        webhook_data: Optional[Dict[str, Any]] = None
    ) -> PaymentResult:
        """Simple payment verification - for now just return pending"""
        try:
            logger.info(f"Verifying Payme payment: {payment_id}")
            
            # For now, we'll implement manual verification
            # In production, you'd implement proper webhook handling
            return PaymentResult(
                success=True,
                payment_id=payment_id,
                status=PaymentStatus.PENDING,
                metadata={"provider": "payme", "note": "Manual verification required"}
            )
            
        except Exception as e:
            logger.error(f"Payme payment verification error: {e}")
            return PaymentResult(
                success=False,
                error_message="Payment verification failed"
            )
    
    async def cancel_payment(self, payment_id: str) -> bool:
        """Cancel payment"""
        try:
            logger.info(f"Cancelled Payme payment: {payment_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling Payme payment: {e}")
            return False
    
    def validate_webhook(
        self,
        webhook_data: Dict[str, Any],
        signature: Optional[str] = None
    ) -> bool:
        """Basic webhook validation"""
        try:
            # For now, accept all webhooks - implement proper validation later
            return True
        except Exception as e:
            logger.error(f"Webhook validation error: {e}")
            return False
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return "payme"


class SimpleClickProvider(BasePaymentProvider):
    """Simplified Click payment provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.merchant_id = config.get("merchant_id", "test_merchant")
        self.service_id = config.get("service_id", "test_service")
        self.secret_key = config.get("secret_key", "test_secret")
        self.base_url = "https://my.click.uz" if self.is_sandbox else "https://my.click.uz"
    
    async def create_payment(
        self,
        amount_usd: float,
        user_id: int,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentResult:
        """Create simple Click payment"""
        try:
            # Convert USD to UZS (approximate rate)
            amount_uzs = int(amount_usd * 12000)  # Amount in UZS
            
            # Create simple payment URL
            payment_url = (
                f"{self.base_url}/pay?"
                f"merchant_id={self.merchant_id}&"
                f"service_id={self.service_id}&"
                f"amount={amount_uzs}&"
                f"transaction_param={user_id}_{int(time.time())}&"
                f"return_url=https://t.me/your_bot_username"
            )
            
            payment_id = f"click_{user_id}_{int(time.time())}"
            
            logger.info(f"Created Click payment: {payment_id} for user {user_id}")
            
            return PaymentResult(
                success=True,
                payment_id=payment_id,
                payment_url=payment_url,
                status=PaymentStatus.PENDING,
                metadata={
                    "amount_uzs": amount_uzs,
                    "amount_usd": amount_usd,
                    "provider": "click"
                }
            )
            
        except Exception as e:
            logger.error(f"Click payment creation error: {e}")
            return PaymentResult(
                success=False,
                error_message="Payment creation failed"
            )
    
    async def verify_payment(
        self,
        payment_id: str,
        webhook_data: Optional[Dict[str, Any]] = None
    ) -> PaymentResult:
        """Simple payment verification"""
        try:
            logger.info(f"Verifying Click payment: {payment_id}")
            
            # For now, we'll implement manual verification
            return PaymentResult(
                success=True,
                payment_id=payment_id,
                status=PaymentStatus.PENDING,
                metadata={"provider": "click", "note": "Manual verification required"}
            )
            
        except Exception as e:
            logger.error(f"Click payment verification error: {e}")
            return PaymentResult(
                success=False,
                error_message="Payment verification failed"
            )
    
    async def cancel_payment(self, payment_id: str) -> bool:
        """Cancel payment"""
        try:
            logger.info(f"Cancelled Click payment: {payment_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling Click payment: {e}")
            return False
    
    def validate_webhook(
        self,
        webhook_data: Dict[str, Any],
        signature: Optional[str] = None
    ) -> bool:
        """Basic webhook validation"""
        try:
            # For now, accept all webhooks - implement proper validation later
            return True
        except Exception as e:
            logger.error(f"Webhook validation error: {e}")
            return False
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return "click"


class ManualPaymentProvider(BasePaymentProvider):
    """Manual payment provider for testing and manual verification"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.admin_contact = config.get("admin_contact", "@admin")
        self.instructions = config.get("instructions", "Contact admin for payment")
    
    async def create_payment(
        self,
        amount_usd: float,
        user_id: int,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentResult:
        """Create manual payment instruction"""
        try:
            payment_id = f"manual_{user_id}_{int(time.time())}"
            
            logger.info(f"Created manual payment: {payment_id} for user {user_id}")
            
            return PaymentResult(
                success=True,
                payment_id=payment_id,
                payment_url=None,
                status=PaymentStatus.PENDING,
                metadata={
                    "amount_usd": amount_usd,
                    "provider": "manual",
                    "admin_contact": self.admin_contact,
                    "instructions": self.instructions
                }
            )
            
        except Exception as e:
            logger.error(f"Manual payment creation error: {e}")
            return PaymentResult(
                success=False,
                error_message="Payment creation failed"
            )
    
    async def verify_payment(
        self,
        payment_id: str,
        webhook_data: Optional[Dict[str, Any]] = None
    ) -> PaymentResult:
        """Manual payment verification"""
        try:
            logger.info(f"Verifying manual payment: {payment_id}")
            
            # Manual payments require admin verification
            return PaymentResult(
                success=True,
                payment_id=payment_id,
                status=PaymentStatus.PENDING,
                metadata={"provider": "manual", "note": "Admin verification required"}
            )
            
        except Exception as e:
            logger.error(f"Manual payment verification error: {e}")
            return PaymentResult(
                success=False,
                error_message="Payment verification failed"
            )
    
    async def cancel_payment(self, payment_id: str) -> bool:
        """Cancel payment"""
        try:
            logger.info(f"Cancelled manual payment: {payment_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling manual payment: {e}")
            return False
    
    def validate_webhook(
        self,
        webhook_data: Dict[str, Any],
        signature: Optional[str] = None
    ) -> bool:
        """Manual payments don't use webhooks"""
        return False
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return "manual"

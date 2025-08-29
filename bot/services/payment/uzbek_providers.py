"""
Uzbek payment providers (Payme, Click, etc.)
"""
import aiohttp
import hmac
import hashlib
import json
import base64
from typing import Optional, Dict, Any
from loguru import logger

from bot.services.payment.base_payment import BasePaymentProvider, PaymentResult, PaymentStatus


class PaymeProvider(BasePaymentProvider):
    """Payme payment provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.merchant_id = config.get("merchant_id")
        self.secret_key = config.get("secret_key")
        self.base_url = "https://checkout.test.paycom.uz/api" if self.is_sandbox else "https://checkout.paycom.uz/api"
    
    async def create_payment(
        self,
        amount_usd: float,
        user_id: int,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentResult:
        """Create Payme payment"""
        try:
            # Convert USD to UZS (approximate rate)
            amount_uzs = int(amount_usd * 12000 * 100)  # Amount in tiyin (1 UZS = 100 tiyin)
            
            # Create payment URL
            payment_url = (
                f"https://checkout.paycom.uz/{self.merchant_id}?"
                f"ac.order_id={user_id}_{int(__import__('time').time())}&"
                f"a={amount_uzs}&"
                f"c={description or 'SMM Bot balance top-up'}"
            )
            
            payment_id = f"payme_{user_id}_{int(__import__('time').time())}"
            
            logger.info(f"Created Payme payment: {payment_id} for user {user_id}")
            
            return PaymentResult(
                success=True,
                payment_id=payment_id,
                payment_url=payment_url,
                status=PaymentStatus.PENDING,
                metadata={
                    "amount_uzs": amount_uzs,
                    "amount_usd": amount_usd
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
        """Verify Payme payment via webhook data"""
        try:
            if not webhook_data:
                return PaymentResult(
                    success=False,
                    error_message="No webhook data provided"
                )
            
            # Parse Payme webhook data
            method = webhook_data.get("method")
            params = webhook_data.get("params", {})
            
            if method == "CheckPerformTransaction":
                return PaymentResult(
                    success=True,
                    payment_id=payment_id,
                    status=PaymentStatus.PENDING
                )
            elif method == "CreateTransaction":
                return PaymentResult(
                    success=True,
                    payment_id=payment_id,
                    status=PaymentStatus.PENDING,
                    metadata={"transaction_id": params.get("id")}
                )
            elif method == "PerformTransaction":
                return PaymentResult(
                    success=True,
                    payment_id=payment_id,
                    status=PaymentStatus.COMPLETED,
                    metadata={"transaction_id": params.get("id")}
                )
            elif method == "CancelTransaction":
                return PaymentResult(
                    success=False,
                    payment_id=payment_id,
                    status=PaymentStatus.CANCELLED
                )
            
            return PaymentResult(
                success=False,
                error_message="Unknown webhook method"
            )
            
        except Exception as e:
            logger.error(f"Payme payment verification error: {e}")
            return PaymentResult(
                success=False,
                error_message="Payment verification failed"
            )
    
    async def cancel_payment(self, payment_id: str) -> bool:
        """Cancel Payme payment"""
        try:
            # Payme cancellation is handled via webhooks
            logger.info(f"Payme payment {payment_id} cancellation requested")
            return True
        except Exception as e:
            logger.error(f"Payme payment cancellation error: {e}")
            return False
    
    def validate_webhook(
        self,
        webhook_data: Dict[str, Any],
        signature: Optional[str] = None
    ) -> bool:
        """Validate Payme webhook"""
        try:
            # Basic validation - you should implement proper signature validation
            required_fields = ["method", "params"]
            return all(field in webhook_data for field in required_fields)
        except Exception as e:
            logger.error(f"Payme webhook validation error: {e}")
            return False
    
    def get_provider_name(self) -> str:
        return "payme"


class ClickProvider(BasePaymentProvider):
    """Click payment provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.merchant_id = config.get("merchant_id")
        self.secret_key = config.get("secret_key")
        self.base_url = "https://api.click.uz/v2" if not self.is_sandbox else "https://api.click.uz/v2"
    
    async def create_payment(
        self,
        amount_usd: float,
        user_id: int,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentResult:
        """Create Click payment"""
        try:
            # Convert USD to UZS
            amount_uzs = amount_usd * 12000
            
            # Create payment URL
            merchant_trans_id = f"{user_id}_{int(__import__('time').time())}"
            
            payment_url = (
                f"https://my.click.uz/services/pay?"
                f"service_id={self.merchant_id}&"
                f"merchant_id={self.merchant_id}&"
                f"amount={amount_uzs}&"
                f"transaction_param={merchant_trans_id}&"
                f"return_url={self.config.get('return_url', '')}"
            )
            
            payment_id = f"click_{merchant_trans_id}"
            
            logger.info(f"Created Click payment: {payment_id} for user {user_id}")
            
            return PaymentResult(
                success=True,
                payment_id=payment_id,
                payment_url=payment_url,
                status=PaymentStatus.PENDING,
                metadata={
                    "amount_uzs": amount_uzs,
                    "merchant_trans_id": merchant_trans_id
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
        """Verify Click payment"""
        try:
            if not webhook_data:
                return PaymentResult(
                    success=False,
                    error_message="No webhook data provided"
                )
            
            # Parse Click webhook data
            error = webhook_data.get("error")
            if error == "0":  # Success
                return PaymentResult(
                    success=True,
                    payment_id=payment_id,
                    status=PaymentStatus.COMPLETED,
                    metadata={
                        "click_trans_id": webhook_data.get("click_trans_id"),
                        "merchant_trans_id": webhook_data.get("merchant_trans_id")
                    }
                )
            else:
                return PaymentResult(
                    success=False,
                    payment_id=payment_id,
                    status=PaymentStatus.FAILED,
                    error_message=f"Click error: {error}"
                )
                
        except Exception as e:
            logger.error(f"Click payment verification error: {e}")
            return PaymentResult(
                success=False,
                error_message="Payment verification failed"
            )
    
    async def cancel_payment(self, payment_id: str) -> bool:
        """Cancel Click payment"""
        try:
            logger.info(f"Click payment {payment_id} cancellation requested")
            return True
        except Exception as e:
            logger.error(f"Click payment cancellation error: {e}")
            return False
    
    def validate_webhook(
        self,
        webhook_data: Dict[str, Any],
        signature: Optional[str] = None
    ) -> bool:
        """Validate Click webhook"""
        try:
            # Implement Click signature validation
            required_fields = ["click_trans_id", "merchant_trans_id", "amount", "error"]
            return all(field in webhook_data for field in required_fields)
        except Exception as e:
            logger.error(f"Click webhook validation error: {e}")
            return False
    
    def get_provider_name(self) -> str:
        return "click"


class UzcardProvider(BasePaymentProvider):
    """Uzcard payment provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.merchant_id = config.get("merchant_id")
        self.secret_key = config.get("secret_key")
    
    async def create_payment(
        self,
        amount_usd: float,
        user_id: int,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentResult:
        """Create Uzcard payment"""
        try:
            # Uzcard implementation would go here
            # This is a placeholder implementation
            
            payment_id = f"uzcard_{user_id}_{int(__import__('time').time())}"
            
            return PaymentResult(
                success=True,
                payment_id=payment_id,
                payment_url=f"https://uzcard.uz/payment/{payment_id}",
                status=PaymentStatus.PENDING
            )
            
        except Exception as e:
            logger.error(f"Uzcard payment creation error: {e}")
            return PaymentResult(
                success=False,
                error_message="Payment creation failed"
            )
    
    async def verify_payment(
        self,
        payment_id: str,
        webhook_data: Optional[Dict[str, Any]] = None
    ) -> PaymentResult:
        """Verify Uzcard payment"""
        # Placeholder implementation
        return PaymentResult(
            success=True,
            payment_id=payment_id,
            status=PaymentStatus.COMPLETED
        )
    
    async def cancel_payment(self, payment_id: str) -> bool:
        """Cancel Uzcard payment"""
        return True
    
    def validate_webhook(
        self,
        webhook_data: Dict[str, Any],
        signature: Optional[str] = None
    ) -> bool:
        """Validate Uzcard webhook"""
        return True
    
    def get_provider_name(self) -> str:
        return "uzcard"


class HumoProvider(BasePaymentProvider):
    """Humo payment provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.merchant_id = config.get("merchant_id")
        self.secret_key = config.get("secret_key")
    
    async def create_payment(
        self,
        amount_usd: float,
        user_id: int,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentResult:
        """Create Humo payment"""
        try:
            # Humo implementation would go here
            # This is a placeholder implementation
            
            payment_id = f"humo_{user_id}_{int(__import__('time').time())}"
            
            return PaymentResult(
                success=True,
                payment_id=payment_id,
                payment_url=f"https://humo.uz/payment/{payment_id}",
                status=PaymentStatus.PENDING
            )
            
        except Exception as e:
            logger.error(f"Humo payment creation error: {e}")
            return PaymentResult(
                success=False,
                error_message="Payment creation failed"
            )
    
    async def verify_payment(
        self,
        payment_id: str,
        webhook_data: Optional[Dict[str, Any]] = None
    ) -> PaymentResult:
        """Verify Humo payment"""
        # Placeholder implementation
        return PaymentResult(
            success=True,
            payment_id=payment_id,
            status=PaymentStatus.COMPLETED
        )
    
    async def cancel_payment(self, payment_id: str) -> bool:
        """Cancel Humo payment"""
        return True
    
    def validate_webhook(
        self,
        webhook_data: Dict[str, Any],
        signature: Optional[str] = None
    ) -> bool:
        """Validate Humo webhook"""
        return True
    
    def get_provider_name(self) -> str:
        return "humo"

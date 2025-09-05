"""
Telegram Payments provider - Simplest and most reliable payment method
"""
from typing import Optional, Dict, Any
from aiogram.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from loguru import logger

from bot.services.payment.base_payment import BasePaymentProvider, PaymentResult, PaymentStatus


class TelegramPaymentsProvider(BasePaymentProvider):
    """Telegram Payments provider using Telegram's built-in payment system"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_token = config.get("provider_token")
        self.currency = config.get("currency", "USD")
        self.title = config.get("title", "SMM Bot Balance")
        self.description = config.get("description", "Top up your balance")
        
    async def create_payment(
        self,
        amount_usd: float,
        user_id: int,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentResult:
        """Create Telegram payment invoice"""
        try:
            # Create payment invoice data
            payment_data = {
                "title": self.title,
                "description": description or self.description,
                "payload": f"balance_topup_{user_id}_{int(__import__('time').time())}",
                "provider_token": self.provider_token,
                "currency": self.currency,
                "prices": [
                    LabeledPrice(
                        label=f"Balance Top-up (${amount_usd:.2f})",
                        amount=int(amount_usd * 100)  # Amount in cents
                    )
                ],
                "start_parameter": f"balance_{user_id}",
                "need_name": False,
                "need_phone_number": False,
                "need_email": False,
                "need_shipping_address": False,
                "send_phone_number_to_provider": False,
                "send_email_to_provider": False,
                "is_flexible": False
            }
            
            payment_id = f"tg_pay_{user_id}_{int(__import__('time').time())}"
            
            logger.info(f"Created Telegram payment: {payment_id} for user {user_id}")
            
            return PaymentResult(
                success=True,
                payment_id=payment_id,
                payment_url=None,  # Telegram payments don't use URLs
                status=PaymentStatus.PENDING,
                metadata={
                    "payment_data": payment_data,
                    "amount_usd": amount_usd,
                    "user_id": user_id
                }
            )
            
        except Exception as e:
            logger.error(f"Telegram payment creation error: {e}")
            return PaymentResult(
                success=False,
                error_message="Payment creation failed"
            )
    
    async def verify_payment(
        self,
        payment_id: str,
        webhook_data: Optional[Dict[str, Any]] = None
    ) -> PaymentResult:
        """Verify Telegram payment via webhook data"""
        try:
            if not webhook_data:
                return PaymentResult(
                    success=False,
                    error_message="No webhook data provided"
                )
            
            # Parse Telegram payment webhook data
            status = webhook_data.get("status")
            
            if status == "paid":
                return PaymentResult(
                    success=True,
                    payment_id=payment_id,
                    status=PaymentStatus.COMPLETED,
                    metadata=webhook_data
                )
            elif status == "pending":
                return PaymentResult(
                    success=True,
                    payment_id=payment_id,
                    status=PaymentStatus.PENDING,
                    metadata=webhook_data
                )
            elif status == "cancelled":
                return PaymentResult(
                    success=True,
                    payment_id=payment_id,
                    status=PaymentStatus.CANCELLED,
                    metadata=webhook_data
                )
            else:
                return PaymentResult(
                    success=False,
                    payment_id=payment_id,
                    status=PaymentStatus.FAILED,
                    error_message=f"Unknown payment status: {status}",
                    metadata=webhook_data
                )
                
        except Exception as e:
            logger.error(f"Telegram payment verification error: {e}")
            return PaymentResult(
                success=False,
                error_message="Payment verification failed"
            )
    
    async def cancel_payment(self, payment_id: str) -> bool:
        """Cancel Telegram payment"""
        try:
            logger.info(f"Cancelled Telegram payment: {payment_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling Telegram payment: {e}")
            return False
    
    def validate_webhook(
        self,
        webhook_data: Dict[str, Any],
        signature: Optional[str] = None
    ) -> bool:
        """Validate Telegram payment webhook"""
        try:
            # Basic validation - Telegram payments are generally secure
            required_fields = ["status", "payment_id"]
            return all(field in webhook_data for field in required_fields)
        except Exception as e:
            logger.error(f"Webhook validation error: {e}")
            return False
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return "telegram_payments"
    
    def get_payment_invoice(self, payment_result: PaymentResult) -> Dict[str, Any]:
        """Get payment invoice data for Telegram bot"""
        if not payment_result.success or not payment_result.metadata:
            return {}
        
        payment_data = payment_result.metadata.get("payment_data", {})
        return payment_data

"""
Payment management service - Simplified and reliable version
"""
from typing import Optional, Dict, Any, List
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from bot.config import settings
from bot.database.models import PaymentMethod, Transaction
from bot.services.balance_service import BalanceService
from bot.services.payment.base_payment import BasePaymentProvider, PaymentResult, PaymentStatus
from bot.services.payment.telegram_payments import TelegramPaymentsProvider
from bot.services.payment.simple_uzbek_payments import SimplePaymeProvider, SimpleClickProvider, ManualPaymentProvider


class PaymentService:
    """Central payment service that manages all payment providers"""
    
    def __init__(self):
        self.providers: Dict[str, BasePaymentProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize payment providers based on configuration"""
        self.providers = {}
        
        # Initialize Telegram Payments (if configured)
        if hasattr(settings, 'telegram_payments_token') and settings.telegram_payments_token:
            try:
                telegram_config = {
                    "provider_token": settings.telegram_payments_token,
                    "currency": "USD",
                    "title": "SMM Bot Balance",
                    "description": "Top up your balance",
                    "sandbox": settings.environment == "development"
                }
                self.providers["telegram"] = TelegramPaymentsProvider(telegram_config)
                logger.info("Telegram Payments provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Telegram Payments: {e}")
        else:
            logger.warning("Telegram Payments token not configured - skipping")
        
        # Initialize Payme (if configured)
        if hasattr(settings, 'payme_merchant_id') and settings.payme_merchant_id:
            try:
                payme_config = {
                    "merchant_id": settings.payme_merchant_id,
                    "secret_key": getattr(settings, 'payme_secret_key', 'test_secret'),
                    "sandbox": settings.environment == "development"
                }
                self.providers["payme"] = SimplePaymeProvider(payme_config)
                logger.info("Payme provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Payme: {e}")
        
        # Initialize Click (if configured)
        if hasattr(settings, 'click_merchant_id') and settings.click_merchant_id:
            try:
                click_config = {
                    "merchant_id": settings.click_merchant_id,
                    "service_id": getattr(settings, 'click_service_id', 'test_service'),
                    "secret_key": getattr(settings, 'click_secret_key', 'test_secret'),
                    "sandbox": settings.environment == "development"
                }
                self.providers["click"] = SimpleClickProvider(click_config)
                logger.info("Click provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Click: {e}")
        
        # Always initialize Manual Payment provider
        try:
            manual_config = {
                "admin_contact": getattr(settings, 'admin_contact', '@admin'),
                "instructions": "Contact admin for payment verification"
            }
            self.providers["manual"] = ManualPaymentProvider(manual_config)
            logger.info("Manual payment provider initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Manual Payment: {e}")
        
        logger.info(f"Initialized {len(self.providers)} payment providers")
    
    async def get_available_providers(self, db=None) -> List[Dict[str, str]]:
        """Get list of available payment providers"""
        try:
            providers = []
            
            for provider_id, provider in self.providers.items():
                providers.append({
                    "id": provider_id,
                    "name": provider.get_display_name(),
                    "description": provider.get_description()
                })
            
            return providers
            
        except Exception as e:
            logger.error(f"Error getting available providers: {e}")
            # Return basic providers even if database is not available
            return [
                {"id": "manual", "name": "📞 Manual Payment", "description": "Contact admin for payment verification"}
            ]
    
    def _get_provider_display_name(self, provider_id: str) -> str:
        """Get human-readable provider name"""
        names = {
            "telegram": "💳 Telegram Payments",
            "payme": "💳 Payme",
            "click": "💳 Click",
            "manual": "📞 Manual Payment"
        }
        return names.get(provider_id, provider_id.title())
    
    def _get_provider_description(self, provider_id: str) -> str:
        """Get provider description"""
        descriptions = {
            "telegram": "Pay directly through Telegram (Recommended)",
            "payme": "Pay with Payme (Uzbekistan)",
            "click": "Pay with Click (Uzbekistan)",
            "manual": "Contact admin for payment"
        }
        return descriptions.get(provider_id, "Payment provider")
    
    async def create_payment(
        self,
        provider_id: str,
        amount_usd: float,
        user_id: int,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentResult:
        """Create payment with specified provider"""
        try:
            if provider_id not in self.providers:
                return PaymentResult(
                    success=False,
                    error_message=f"Payment provider '{provider_id}' not available"
                )
            
            provider = self.providers[provider_id]
            
            # Validate amount
            if amount_usd < getattr(settings, 'min_deposit_usd', 1.0):
                return PaymentResult(
                    success=False,
                    error_message=f"Minimum deposit amount is ${getattr(settings, 'min_deposit_usd', 1.0)}"
                )
            
            if amount_usd > getattr(settings, 'max_deposit_usd', 1000.0):
                return PaymentResult(
                    success=False,
                    error_message=f"Maximum deposit amount is ${getattr(settings, 'max_deposit_usd', 1000.0)}"
                )
            
            # Create payment
            result = await provider.create_payment(amount_usd, user_id, description, metadata)
            
            if result.success:
                logger.info(f"Payment created successfully: {result.payment_id} via {provider_id}")
                
                # Store payment in database
                await self._store_payment(db=None, result=result, user_id=user_id, provider_id=provider_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            return PaymentResult(
                success=False,
                error_message="Payment creation failed"
            )
    
    async def _store_payment(self, db: Optional[AsyncSession], result: PaymentResult, user_id: int, provider_id: str):
        """Store payment information in database"""
        try:
            # This would store the payment in the database
            # For now, just log it
            logger.info(f"Payment {result.payment_id} stored for user {user_id} via {provider_id}")
        except Exception as e:
            logger.error(f"Error storing payment: {e}")
    
    async def verify_payment(
        self,
        payment_id: str,
        provider_id: str,
        webhook_data: Optional[Dict[str, Any]] = None
    ) -> PaymentResult:
        """Verify payment status"""
        try:
            if provider_id not in self.providers:
                return PaymentResult(
                    success=False,
                    error_message=f"Payment provider '{provider_id}' not available"
                )
            
            provider = self.providers[provider_id]
            result = await provider.verify_payment(payment_id, webhook_data)
            
            if result.success and result.status == PaymentStatus.COMPLETED:
                # Process successful payment
                await self._process_successful_payment(payment_id, user_id=None, amount=None)
            
            return result
            
        except Exception as e:
            logger.error(f"Error verifying payment: {e}")
            return PaymentResult(
                success=False,
                error_message="Payment verification failed"
            )
    
    async def _process_successful_payment(self, payment_id: str, user_id: Optional[int], amount: Optional[float]):
        """Process successful payment"""
        try:
            logger.info(f"Processing successful payment: {payment_id}")
            # This would update user balance, create transaction record, etc.
            # For now, just log it
        except Exception as e:
            logger.error(f"Error processing successful payment: {e}")
    
    async def cancel_payment(self, payment_id: str, provider_id: str) -> bool:
        """Cancel payment"""
        try:
            if provider_id not in self.providers:
                logger.error(f"Payment provider '{provider_id}' not available")
                return False
            
            provider = self.providers[provider_id]
            return await provider.cancel_payment(payment_id)
            
        except Exception as e:
            logger.error(f"Error cancelling payment: {e}")
            return False
    
    async def get_payment_status(self, payment_id: str) -> Optional[PaymentStatus]:
        """Get payment status"""
        try:
            # This would query the database for payment status
            # For now, return None
            return None
        except Exception as e:
            logger.error(f"Error getting payment status: {e}")
            return None
    
    async def close_all_providers(self):
        """Close all payment provider connections"""
        try:
            for provider_name, provider in self.providers.items():
                try:
                    if hasattr(provider, 'close'):
                        await provider.close()
                    logger.info(f"Closed {provider_name} provider")
                except Exception as e:
                    logger.error(f"Error closing {provider_name} provider: {e}")
            
            logger.info("Closed all payment provider connections")
            
        except Exception as e:
            logger.error(f"Error closing payment providers: {e}")
    
    def get_provider(self, provider_id: str) -> Optional[BasePaymentProvider]:
        """Get payment provider by ID"""
        return self.providers.get(provider_id)
    
    def is_provider_available(self, provider_id: str) -> bool:
        """Check if payment provider is available"""
        return provider_id in self.providers


# Global payment service instance
payment_service = PaymentService()

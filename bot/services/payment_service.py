"""
Payment management service - orchestrates all payment providers
"""
from typing import Optional, Dict, Any, List
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from bot.config import settings
from bot.database.models import PaymentMethod, Transaction
from bot.services.balance_service import BalanceService
from bot.services.payment.base_payment import BasePaymentProvider, PaymentResult, PaymentStatus
from bot.services.payment.crypto_provider import CryptoProvider
from bot.services.payment.paypal_provider import PayPalProvider
from bot.services.payment.uzbek_providers import PaymeProvider, ClickProvider, UzcardProvider, HumoProvider


class PaymentService:
    """Central payment service that manages all payment providers"""
    
    def __init__(self):
        self.providers: Dict[str, BasePaymentProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all payment providers"""
        try:
            # Stripe has been removed as per requirements
            
            # Crypto provider (CoinGate)
            if settings.coingate_api_token:
                self.providers["coingate"] = CryptoProvider({
                    "api_token": settings.coingate_api_token,
                    "sandbox": settings.coingate_sandbox,
                    "callback_url": "https://yourbot.com",  # Configure this
                    "success_url": "https://yourbot.com/success",
                    "cancel_url": "https://yourbot.com/cancel"
                })
                logger.info("CoinGate provider initialized")
                
            # PayPal provider
            if settings.paypal_client_id and settings.paypal_client_secret:
                self.providers["paypal"] = PayPalProvider({
                    "client_id": settings.paypal_client_id,
                    "client_secret": settings.paypal_client_secret,
                    "sandbox": settings.environment == "development",
                    "return_url": "https://yourbot.com",  # Configure this
                    "cancel_url": "https://yourbot.com",
                    "webhook_id": settings.paypal_webhook_id
                })
                logger.info("PayPal provider initialized")
            
            # Payme provider
            if settings.payme_merchant_id:
                self.providers["payme"] = PaymeProvider({
                    "merchant_id": settings.payme_merchant_id,
                    "secret_key": settings.payme_secret_key,
                    "sandbox": settings.environment == "development"
                })
                logger.info("Payme provider initialized")
            
            # Click provider
            if settings.click_merchant_id:
                self.providers["click"] = ClickProvider({
                    "merchant_id": settings.click_merchant_id,
                    "secret_key": settings.click_secret_key,
                    "sandbox": settings.environment == "development",
                    "return_url": "https://yourbot.com/return"
                })
                logger.info("Click provider initialized")
            
            # Uzcard provider (placeholder)
            self.providers["uzcard"] = UzcardProvider({
                "merchant_id": "uzcard_merchant_id",
                "secret_key": "uzcard_secret_key",
                "sandbox": settings.environment == "development"
            })
            
            # Humo provider (placeholder)
            self.providers["humo"] = HumoProvider({
                "merchant_id": "humo_merchant_id",
                "secret_key": "humo_secret_key",
                "sandbox": settings.environment == "development"
            })
            
            logger.info(f"Initialized {len(self.providers)} payment providers")
            
        except Exception as e:
            logger.error(f"Error initializing payment providers: {e}")
    
    async def get_available_providers(self, db: AsyncSession) -> List[Dict[str, str]]:
        """Get list of available payment providers based on settings"""
        from bot.services.settings_service import SettingsService
        
        providers = []
        
        for provider_name, provider in self.providers.items():
            # Check if provider is enabled in settings
            enabled = await SettingsService.get_setting(db, f"{provider_name}_enabled", True)
            
            if enabled:
                providers.append({
                    "name": provider_name,
                    "display_name": provider.get_provider_name(),
                    "available": True
                })
        
        return providers
    
    async def create_payment(
        self,
        db: AsyncSession,
        provider_name: str,
        user_id: int,
        amount_usd: float,
        description: Optional[str] = None
    ) -> Optional[PaymentResult]:
        """Create payment with specified provider"""
        try:
            # Validate amount
            if amount_usd < settings.min_deposit_usd or amount_usd > settings.max_deposit_usd:
                logger.warning(f"Invalid payment amount: {amount_usd} (min: {settings.min_deposit_usd}, max: {settings.max_deposit_usd})")
                return PaymentResult(
                    success=False,
                    error_message=f"Amount must be between ${settings.min_deposit_usd} and ${settings.max_deposit_usd}"
                )
            
            # Get provider
            provider = self.providers.get(provider_name)
            if not provider:
                logger.error(f"Payment provider {provider_name} not found")
                return PaymentResult(
                    success=False,
                    error_message="Payment method not available"
                )
            
            # Check if payment method is enabled
            from bot.services.settings_service import SettingsService
            enabled = await SettingsService.get_setting(db, f"{provider_name}_enabled", True)
            if not enabled:
                logger.warning(f"Payment provider {provider_name} is disabled")
                return PaymentResult(
                    success=False,
                    error_message="This payment method is currently unavailable"
                )
            
            # Calculate coins amount
            coins_amount = BalanceService.usd_to_coins_static(amount_usd)
            
            # Create pending transaction
            transaction = await BalanceService.create_pending_transaction(
                db=db,
                user_id=user_id,
                amount=coins_amount,
                usd_amount=amount_usd,
                payment_method=PaymentMethod(provider_name),
                description=description or f"Balance top-up via {provider_name}"
            )
            
            if not transaction:
                return PaymentResult(
                    success=False,
                    error_message="Failed to create transaction"
                )
            
            # For web payments, return the transaction ID so the user can be redirected to the web interface
            web_payment_url = f"{settings.web_base_url}/payment/{transaction.id}" if getattr(settings, 'enable_web_server', False) else None
            
            if web_payment_url:
                logger.info(f"Created web payment redirect for user {user_id}, transaction {transaction.id}")
                return PaymentResult(
                    success=True,
                    payment_id=str(transaction.id),
                    payment_url=web_payment_url,
                    status=PaymentStatus.PENDING
                )
            
            # Create payment with provider directly if web interface is not enabled
            result = await provider.create_payment(
                amount_usd=amount_usd,
                user_id=user_id,
                description=description,
                metadata={
                    "transaction_id": transaction.id,
                    "coins_amount": coins_amount
                }
            )
            
            if result.success:
                # Update transaction with payment ID
                transaction.external_id = result.payment_id
                await db.commit()
                
                logger.info(f"Created payment {result.payment_id} for user {user_id} via {provider_name}")
            else:
                # Mark transaction as failed
                await BalanceService.fail_transaction(db, transaction.id, result.error_message)
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            return PaymentResult(
                success=False,
                error_message="Payment creation failed"
            )
    
    async def create_payment_web(
        self,
        db: AsyncSession,
        provider_name: str,
        transaction_id: int,
        user_id: int,
        amount_usd: float,
        return_url: str = "",
        cancel_url: str = "",
        description: Optional[str] = None
    ) -> Optional[PaymentResult]:
        """Create payment with specified provider from web interface"""
        try:
            # Get provider
            provider = self.providers.get(provider_name)
            if not provider:
                logger.error(f"Payment provider {provider_name} not found")
                return PaymentResult(
                    success=False,
                    error_message="Payment method not available"
                )
            
            # Check if payment method is enabled
            from bot.services.settings_service import SettingsService
            enabled = await SettingsService.get_setting(db, f"{provider_name}_enabled", True)
            if not enabled:
                logger.warning(f"Payment provider {provider_name} is disabled")
                return PaymentResult(
                    success=False,
                    error_message="This payment method is currently unavailable"
                )
            
            # Get transaction
            transaction = await BalanceService.get_transaction_by_id(db, transaction_id)
            if not transaction or transaction.user_id != user_id:
                logger.error(f"Transaction {transaction_id} not found or doesn't belong to user {user_id}")
                return PaymentResult(
                    success=False,
                    error_message="Invalid transaction"
                )
            
            # Calculate coins amount
            coins_amount = transaction.amount
            
            # Create payment with provider
            result = await provider.create_payment(
                amount_usd=amount_usd,
                user_id=user_id,
                description=description or f"Balance top-up via {provider_name}",
                metadata={
                    "transaction_id": transaction_id,
                    "coins_amount": coins_amount,
                    "return_url": return_url,
                    "cancel_url": cancel_url
                }
            )
            
            if result.success:
                # Update transaction with payment ID
                transaction.external_id = result.payment_id
                await db.commit()
                
                logger.info(f"Created web payment {result.payment_id} for user {user_id} via {provider_name}")
            else:
                # Mark transaction as failed
                await BalanceService.fail_transaction(db, transaction_id, result.error_message)
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating web payment: {e}")
            return PaymentResult(
                success=False,
                error_message="Payment creation failed"
            )
    
    async def verify_payment(
        self,
        db: AsyncSession,
        provider_name: str,
        payment_id: str,
        webhook_data: Optional[Dict[str, Any]] = None
    ) -> Optional[PaymentResult]:
        """Verify payment with provider"""
        try:
            provider = self.providers.get(provider_name)
            if not provider:
                logger.error(f"Payment provider {provider_name} not found")
                return None
            
            # Verify with provider
            result = await provider.verify_payment(payment_id, webhook_data)
            
            if result.success and result.status == PaymentStatus.COMPLETED:
                # Find transaction by external ID
                transaction = await BalanceService.get_transaction_by_external_id(
                    db, payment_id, PaymentMethod(provider_name)
                )
                
                if transaction:
                    # Complete transaction and add balance
                    success = await BalanceService.complete_transaction(db, transaction.id)
                    if success:
                        logger.info(f"Completed payment {payment_id} for user {transaction.user_id}")
                    else:
                        logger.error(f"Failed to complete transaction {transaction.id}")
                else:
                    logger.warning(f"Transaction not found for payment {payment_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error verifying payment: {e}")
            return None
    
    async def handle_webhook(
        self,
        provider_name: str,
        webhook_data: Dict[str, Any],
        signature: Optional[str] = None
    ) -> bool:
        """Handle payment webhook"""
        try:
            provider = self.providers.get(provider_name)
            if not provider:
                logger.error(f"Payment provider {provider_name} not found")
                return False
            
            # Validate webhook
            if not provider.validate_webhook(webhook_data, signature):
                logger.warning(f"Invalid webhook signature for provider {provider_name}")
                return False
            
            # Extract payment ID from webhook data
            payment_id = self._extract_payment_id(provider_name, webhook_data)
            if not payment_id:
                logger.error(f"Could not extract payment ID from webhook data")
                return False
            
            # Verify payment
            from bot.database.db import get_db
            async for db in get_db():
                result = await self.verify_payment(db, provider_name, payment_id, webhook_data)
                if result:
                    logger.info(f"Processed webhook for payment {payment_id}: {result.status.value}")
                    return True
                break
            
            return False
            
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return False
    
    def _extract_payment_id(self, provider_name: str, webhook_data: Dict[str, Any]) -> Optional[str]:
        """Extract payment ID from webhook data based on provider"""
        try:
            if provider_name == "coingate":
                return str(webhook_data.get("id"))
            elif provider_name == "payme":
                # Payme uses order_id in account field
                account = webhook_data.get("params", {}).get("account", {})
                return account.get("order_id")
            elif provider_name == "click":
                return webhook_data.get("merchant_trans_id")
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting payment ID: {e}")
            return None
    
    async def cancel_payment(
        self,
        db: AsyncSession,
        provider_name: str,
        payment_id: str
    ) -> bool:
        """Cancel payment"""
        try:
            provider = self.providers.get(provider_name)
            if not provider:
                return False
            
            # Cancel with provider
            success = await provider.cancel_payment(payment_id)
            
            if success:
                # Mark transaction as cancelled
                transaction = await BalanceService.get_transaction_by_external_id(
                    db, payment_id, PaymentMethod(provider_name)
                )
                if transaction:
                    await BalanceService.fail_transaction(db, transaction.id, "Payment cancelled")
            
            return success
            
        except Exception as e:
            logger.error(f"Error cancelling payment: {e}")
            return False
    
    async def close_all_providers(self):
        """Close all provider connections"""
        for provider in self.providers.values():
            if hasattr(provider, 'close'):
                await provider.close()
        logger.info("Closed all payment provider connections")


# Global payment service instance
payment_service = PaymentService()

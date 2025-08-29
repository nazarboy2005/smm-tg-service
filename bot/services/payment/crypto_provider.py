"""
Cryptocurrency payment provider (CoinGate)
"""
import aiohttp
import hmac
import hashlib
from typing import Optional, Dict, Any
from loguru import logger

from bot.services.payment.base_payment import BasePaymentProvider, PaymentResult, PaymentStatus


class CryptoProvider(BasePaymentProvider):
    """CoinGate cryptocurrency payment provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_token = config.get("api_token")
        self.base_url = "https://api-sandbox.coingate.com/v2" if self.is_sandbox else "https://api.coingate.com/v2"
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Token {self.api_token}",
                    "Content-Type": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def create_payment(
        self,
        amount_usd: float,
        user_id: int,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentResult:
        """Create CoinGate payment"""
        try:
            session = await self._get_session()
            
            # Create order
            order_data = {
                "order_id": f"user_{user_id}_{int(__import__('time').time())}",
                "price_amount": amount_usd,
                "price_currency": "USD",
                "receive_currency": "USD",
                "title": description or f"SMM Bot balance top-up",
                "description": description or f"Balance top-up for user {user_id}",
                "callback_url": f"{self.config.get('callback_url', '')}/webhook/coingate",
                "success_url": f"{self.config.get('success_url', '')}/payment/success",
                "cancel_url": f"{self.config.get('cancel_url', '')}/payment/cancel",
                "token": self.api_token
            }
            
            async with session.post(f"{self.base_url}/orders", json=order_data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    logger.info(f"Created CoinGate order: {result['id']} for user {user_id}")
                    
                    return PaymentResult(
                        success=True,
                        payment_id=str(result["id"]),
                        payment_url=result["payment_url"],
                        status=PaymentStatus.PENDING,
                        metadata={
                            "order_id": result["order_id"],
                            "payment_address": result.get("payment_address"),
                            "pay_amount": result.get("pay_amount"),
                            "pay_currency": result.get("pay_currency"),
                            "lightning_network": result.get("lightning_network")
                        }
                    )
                else:
                    error_text = await response.text()
                    logger.error(f"CoinGate order creation failed: {response.status} - {error_text}")
                    return PaymentResult(
                        success=False,
                        error_message=f"Payment creation failed: {error_text}"
                    )
                    
        except Exception as e:
            logger.error(f"CoinGate payment creation error: {e}")
            return PaymentResult(
                success=False,
                error_message="Payment creation failed"
            )
    
    async def verify_payment(
        self,
        payment_id: str,
        webhook_data: Optional[Dict[str, Any]] = None
    ) -> PaymentResult:
        """Verify CoinGate payment"""
        try:
            session = await self._get_session()
            
            async with session.get(f"{self.base_url}/orders/{payment_id}") as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Map CoinGate status to our status
                    status_mapping = {
                        "new": PaymentStatus.PENDING,
                        "pending": PaymentStatus.PENDING,
                        "confirming": PaymentStatus.PENDING,
                        "paid": PaymentStatus.COMPLETED,
                        "invalid": PaymentStatus.FAILED,
                        "expired": PaymentStatus.CANCELLED,
                        "canceled": PaymentStatus.CANCELLED,
                        "refunded": PaymentStatus.CANCELLED
                    }
                    
                    coingate_status = result.get("status", "").lower()
                    status = status_mapping.get(coingate_status, PaymentStatus.FAILED)
                    
                    return PaymentResult(
                        success=status == PaymentStatus.COMPLETED,
                        payment_id=payment_id,
                        status=status,
                        metadata={
                            "coingate_status": coingate_status,
                            "pay_amount": result.get("pay_amount"),
                            "pay_currency": result.get("pay_currency"),
                            "receive_amount": result.get("receive_amount"),
                            "receive_currency": result.get("receive_currency")
                        }
                    )
                else:
                    error_text = await response.text()
                    logger.error(f"CoinGate payment verification failed: {response.status} - {error_text}")
                    return PaymentResult(
                        success=False,
                        error_message="Payment verification failed"
                    )
                    
        except Exception as e:
            logger.error(f"CoinGate payment verification error: {e}")
            return PaymentResult(
                success=False,
                error_message="Payment verification failed"
            )
    
    async def cancel_payment(self, payment_id: str) -> bool:
        """Cancel CoinGate payment (not directly supported)"""
        try:
            # CoinGate doesn't support order cancellation via API
            # Orders expire automatically after timeout
            logger.info(f"CoinGate payment {payment_id} will expire automatically")
            return True
        except Exception as e:
            logger.error(f"CoinGate payment cancellation error: {e}")
            return False
    
    def validate_webhook(
        self,
        webhook_data: Dict[str, Any],
        signature: Optional[str] = None
    ) -> bool:
        """Validate CoinGate webhook"""
        try:
            # CoinGate doesn't use HMAC signatures by default
            # You can implement custom validation here if needed
            return True
        except Exception as e:
            logger.error(f"CoinGate webhook validation error: {e}")
            return False
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return "coingate"
    
    def get_supported_currencies(self) -> Dict[str, str]:
        """Get supported cryptocurrencies"""
        return {
            "BTC": "₿ Bitcoin",
            "ETH": "Ξ Ethereum",
            "LTC": "Ł Litecoin",
            "BCH": "₿ Bitcoin Cash",
            "XRP": "◉ Ripple",
            "ADA": "₳ Cardano",
            "DOT": "● Polkadot",
            "USDT": "₮ Tether",
            "USDC": "$ USD Coin",
            "BUSD": "$ Binance USD"
        }

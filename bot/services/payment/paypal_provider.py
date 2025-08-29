"""
PayPal payment provider
"""
import aiohttp
import base64
import json
from typing import Optional, Dict, Any
from loguru import logger

from bot.services.payment.base_payment import BasePaymentProvider, PaymentResult, PaymentStatus


class PayPalProvider(BasePaymentProvider):
    """PayPal payment provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        self.base_url = "https://api-m.sandbox.paypal.com" if self.is_sandbox else "https://api-m.paypal.com"
        self.session = None
        self.access_token = None
        self.token_expires_at = 0
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    async def _get_access_token(self) -> Optional[str]:
        """Get PayPal OAuth access token"""
        import time
        
        try:
            # Return cached token if still valid
            if self.access_token and time.time() < self.token_expires_at:
                return self.access_token
            
            session = await self._get_session()
            
            # Create basic auth header
            auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            
            async with session.post(
                f"{self.base_url}/v1/oauth2/token",
                headers={"Authorization": f"Basic {auth}"},
                data="grant_type=client_credentials"
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.access_token = result["access_token"]
                    self.token_expires_at = time.time() + result["expires_in"] - 60  # Buffer of 60 seconds
                    return self.access_token
                else:
                    error_text = await response.text()
                    logger.error(f"PayPal token request failed: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"PayPal token error: {e}")
            return None
    
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
        """Create PayPal payment"""
        try:
            session = await self._get_session()
            token = await self._get_access_token()
            
            if not token:
                return PaymentResult(
                    success=False,
                    error_message="Authentication failed"
                )
            
            # Create order
            order_data = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "reference_id": f"user_{user_id}_{int(__import__('time').time())}",
                    "description": description or f"Balance top-up for user {user_id}",
                    "amount": {
                        "currency_code": "USD",
                        "value": f"{amount_usd:.2f}"
                    },
                    "custom_id": str(metadata.get("transaction_id")) if metadata else None
                }],
                "application_context": {
                    "return_url": f"{self.config.get('return_url', '')}/payment/success",
                    "cancel_url": f"{self.config.get('cancel_url', '')}/payment/cancel"
                }
            }
            
            async with session.post(
                f"{self.base_url}/v2/checkout/orders",
                headers={"Authorization": f"Bearer {token}"},
                json=order_data
            ) as response:
                if response.status in (200, 201):
                    result = await response.json()
                    
                    # Extract approval URL
                    approval_url = None
                    for link in result.get("links", []):
                        if link.get("rel") == "approve":
                            approval_url = link.get("href")
                            break
                    
                    if not approval_url:
                        logger.error(f"PayPal approval URL not found in response: {result}")
                        return PaymentResult(
                            success=False,
                            error_message="Payment URL not found"
                        )
                    
                    logger.info(f"Created PayPal order: {result['id']} for user {user_id}")
                    
                    return PaymentResult(
                        success=True,
                        payment_id=result["id"],
                        payment_url=approval_url,
                        status=PaymentStatus.PENDING,
                        metadata={
                            "order_id": result["id"],
                            "create_time": result.get("create_time")
                        }
                    )
                else:
                    error_text = await response.text()
                    logger.error(f"PayPal order creation failed: {response.status} - {error_text}")
                    return PaymentResult(
                        success=False,
                        error_message=f"Payment creation failed: {error_text}"
                    )
                    
        except Exception as e:
            logger.error(f"PayPal payment creation error: {e}")
            return PaymentResult(
                success=False,
                error_message="Payment creation failed"
            )
    
    async def verify_payment(
        self,
        payment_id: str,
        webhook_data: Optional[Dict[str, Any]] = None
    ) -> PaymentResult:
        """Verify PayPal payment"""
        try:
            session = await self._get_session()
            token = await self._get_access_token()
            
            if not token:
                return PaymentResult(
                    success=False,
                    error_message="Authentication failed"
                )
            
            async with session.get(
                f"{self.base_url}/v2/checkout/orders/{payment_id}",
                headers={"Authorization": f"Bearer {token}"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Map PayPal status to our status
                    status_mapping = {
                        "CREATED": PaymentStatus.PENDING,
                        "SAVED": PaymentStatus.PENDING,
                        "APPROVED": PaymentStatus.PENDING,
                        "VOIDED": PaymentStatus.CANCELLED,
                        "COMPLETED": PaymentStatus.COMPLETED,
                        "PAYER_ACTION_REQUIRED": PaymentStatus.PENDING
                    }
                    
                    paypal_status = result.get("status", "").upper()
                    status = status_mapping.get(paypal_status, PaymentStatus.FAILED)
                    
                    # If payment is approved but not completed, try to capture it
                    if paypal_status == "APPROVED":
                        capture_result = await self._capture_payment(payment_id, token)
                        if capture_result and capture_result.get("status") == "COMPLETED":
                            status = PaymentStatus.COMPLETED
                    
                    return PaymentResult(
                        success=status == PaymentStatus.COMPLETED,
                        payment_id=payment_id,
                        status=status,
                        metadata={
                            "paypal_status": paypal_status,
                            "payer": result.get("payer", {}),
                            "purchase_units": result.get("purchase_units", [])
                        }
                    )
                else:
                    error_text = await response.text()
                    logger.error(f"PayPal payment verification failed: {response.status} - {error_text}")
                    return PaymentResult(
                        success=False,
                        error_message="Payment verification failed"
                    )
                    
        except Exception as e:
            logger.error(f"PayPal payment verification error: {e}")
            return PaymentResult(
                success=False,
                error_message="Payment verification failed"
            )
    
    async def _capture_payment(self, payment_id: str, token: str) -> Optional[Dict[str, Any]]:
        """Capture an approved PayPal payment"""
        try:
            session = await self._get_session()
            
            async with session.post(
                f"{self.base_url}/v2/checkout/orders/{payment_id}/capture",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            ) as response:
                if response.status in (200, 201):
                    result = await response.json()
                    logger.info(f"Captured PayPal payment {payment_id}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"PayPal payment capture failed: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"PayPal payment capture error: {e}")
            return None
    
    async def cancel_payment(self, payment_id: str) -> bool:
        """Cancel PayPal payment"""
        try:
            session = await self._get_session()
            token = await self._get_access_token()
            
            if not token:
                return False
            
            # PayPal doesn't have a direct cancel endpoint for orders
            # We can only check if it's in a state that can be considered cancelled
            async with session.get(
                f"{self.base_url}/v2/checkout/orders/{payment_id}",
                headers={"Authorization": f"Bearer {token}"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    status = result.get("status", "").upper()
                    
                    # If payment is still in CREATED state, we can consider it cancelled
                    # as it will eventually expire
                    if status in ("CREATED", "SAVED"):
                        logger.info(f"PayPal payment {payment_id} is in {status} state and will expire")
                        return True
                    else:
                        logger.warning(f"PayPal payment {payment_id} is in {status} state and cannot be cancelled")
                        return False
                else:
                    logger.error(f"PayPal payment cancel check failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"PayPal payment cancellation error: {e}")
            return False
    
    def validate_webhook(
        self,
        webhook_data: Dict[str, Any],
        signature: Optional[str] = None
    ) -> bool:
        """Validate PayPal webhook"""
        try:
            # PayPal webhook validation requires the webhook ID and webhook event signature
            # This is a simplified version - in production, implement proper signature verification
            if not signature:
                return False
                
            # Extract headers needed for validation
            headers = json.loads(signature)
            webhook_id = self.config.get("webhook_id")
            
            if not webhook_id:
                logger.warning("PayPal webhook ID not configured")
                return False
                
            # In a real implementation, you would verify the signature using PayPal's API
            # For now, we'll just check that the required headers are present
            required_headers = ["PAYPAL-AUTH-ALGO", "PAYPAL-CERT-URL", "PAYPAL-TRANSMISSION-ID", "PAYPAL-TRANSMISSION-SIG", "PAYPAL-TRANSMISSION-TIME"]
            
            for header in required_headers:
                if header not in headers:
                    logger.warning(f"Missing required PayPal webhook header: {header}")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"PayPal webhook validation error: {e}")
            return False
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return "paypal"

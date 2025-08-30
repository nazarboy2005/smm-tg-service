#!/usr/bin/env python3
"""
Simple webhook test without complex dependencies
"""
import asyncio
import aiohttp
from loguru import logger

async def test_webhook_endpoint():
    """Test webhook endpoint accessibility"""
    try:
        logger.info("🌐 Testing webhook endpoint...")
        
        base_url = "https://smm-tg-service-production.up.railway.app"
        endpoints = [
            "/",
            "/health", 
            "/webhook"
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                url = f"{base_url}{endpoint}"
                try:
                    logger.info(f"Testing: {url}")
                    async with session.get(url, timeout=10) as response:
                        logger.info(f"   Status: {response.status}")
                        if response.status == 200:
                            try:
                                data = await response.text()
                                logger.info(f"   Response: {data[:200]}...")
                            except:
                                logger.info("   Response: (binary data)")
                        else:
                            logger.warning(f"   Error: {response.status}")
                except asyncio.TimeoutError:
                    logger.error(f"   Timeout connecting to {url}")
                except Exception as e:
                    logger.error(f"   Connection error: {e}")
        
        # Test POST to webhook (simulating Telegram)
        webhook_url = f"{base_url}/webhook"
        test_update = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "Test",
                    "username": "testuser"
                },
                "chat": {
                    "id": 123456789,
                    "first_name": "Test",
                    "username": "testuser",
                    "type": "private"
                },
                "date": 1693420800,
                "text": "/start"
            }
        }
        
        try:
            logger.info(f"🧪 Testing POST to webhook: {webhook_url}")
            async with session.post(webhook_url, json=test_update, timeout=10) as response:
                logger.info(f"   Webhook POST status: {response.status}")
                if response.status in [200, 201]:
                    data = await response.text()
                    logger.success(f"   Webhook response: {data}")
                else:
                    logger.warning(f"   Webhook error: {response.status}")
        except Exception as e:
            logger.error(f"   Webhook POST error: {e}")
            
    except Exception as e:
        logger.error(f"❌ Webhook test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_webhook_endpoint())
"""ConnectXperts NMS - Webhook Alert Service"""
import logging
from typing import Optional, Dict, Any
import httpx
import json

logger = logging.getLogger(__name__)


class WebhookService:
    """Webhook service for sending alert notifications to external systems."""
    
    async def send_webhook(self, webhook_url: str, payload: Dict[str, Any]) -> Optional[Dict]:
        """Send a webhook notification."""
        if not webhook_url:
            logger.warning("Webhook URL not provided")
            return None
        
        try:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "ConnectXperts-NMS/1.0"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code < 300:
                    logger.info(f"Webhook sent to {webhook_url}")
                    return {"status": "sent", "status_code": response.status_code}
                else:
                    logger.error(f"Webhook error {response.status_code}: {response.text[:200]}")
                    return {"status": "failed", "error": f"HTTP {response.status_code}"}
                    
        except httpx.TimeoutException:
            logger.error(f"Webhook timeout: {webhook_url}")
            return {"status": "failed", "error": "timeout"}
        except Exception as e:
            logger.error(f"Webhook error: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    async def send_discord_webhook(self, webhook_url: str, message: str) -> Optional[Dict]:
        """Send a Discord-compatible webhook."""
        payload = {
            "content": message,
            "username": "ConnectXperts NMS",
            "avatar_url": None
        }
        return await self.send_webhook(webhook_url, payload)
    
    async def send_slack_webhook(self, webhook_url: str, message: str) -> Optional[Dict]:
        """Send a Slack-compatible webhook."""
        payload = {
            "text": message,
            "username": "ConnectXperts NMS"
        }
        return await self.send_webhook(webhook_url, payload)

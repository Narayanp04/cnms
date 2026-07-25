"""ConnectXperts NMS - Telegram Alert Service"""
import logging
from typing import Optional, Dict
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class TelegramService:
    """Telegram bot service for sending alert notifications."""
    
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    async def send_message(self, chat_id: str, message: str) -> Optional[Dict]:
        """Send a message via Telegram bot."""
        if not self._is_configured():
            logger.warning("Telegram not configured. Set TELEGRAM_BOT_TOKEN.")
            return None
        
        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Telegram message sent to {chat_id}")
                    return {"status": "sent", "message_id": result.get("result", {}).get("message_id")}
                else:
                    logger.error(f"Telegram API error: {response.status_code}")
                    return {"status": "failed", "error": response.text}
                    
        except Exception as e:
            logger.error(f"Telegram error: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    async def set_webhook(self, webhook_url: str) -> bool:
        """Set Telegram bot webhook."""
        if not self._is_configured():
            return False
        
        try:
            url = f"{self.api_url}/setWebhook"
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json={"url": webhook_url})
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Telegram webhook error: {str(e)}")
            return False
    
    def _is_configured(self) -> bool:
        """Check if Telegram is configured."""
        return bool(self.bot_token)

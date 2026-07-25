"""ConnectXperts NMS - WhatsApp Cloud API Service"""
import logging
import json
from typing import Optional, Dict, List
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    """WhatsApp Cloud API integration for sending alerts."""
    
    def __init__(self):
        self.api_url = settings.WHATSAPP_API_URL
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.base_url = f"{self.api_url}/{self.phone_number_id}/messages"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def send_message(self, to: str, message: str) -> Optional[Dict]:
        """Send a text message via WhatsApp Cloud API."""
        if not self._is_configured():
            logger.warning("WhatsApp not configured. Set WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_ACCESS_TOKEN")
            return None
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    message_id = result.get("messages", [{}])[0].get("id")
                    logger.info(f"WhatsApp message sent to {to}: {message_id}")
                    return {"status": "sent", "message_id": message_id}
                else:
                    logger.error(f"WhatsApp API error: {response.status_code} - {response.text}")
                    return {"status": "failed", "error": response.text}
                    
        except httpx.TimeoutException:
            logger.error(f"WhatsApp timeout sending to {to}")
            return {"status": "failed", "error": "timeout"}
        except Exception as e:
            logger.error(f"WhatsApp error: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    async def send_template_message(
        self, to: str, template_name: str, 
        template_params: Dict[str, str]
    ) -> Optional[Dict]:
        """Send a template message via WhatsApp Cloud API."""
        if not self._is_configured():
            return None
        
        components = [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": value}
                    for value in template_params.values()
                ]
            }
        ]
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "en"},
                "components": components
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {"status": "sent", "message_id": result.get("messages", [{}])[0].get("id")}
                else:
                    logger.error(f"WhatsApp template error: {response.status_code}")
                    return {"status": "failed", "error": response.text}
                    
        except Exception as e:
            logger.error(f"WhatsApp template error: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    async def send_media_message(
        self, to: str, media_url: str, 
        media_type: str = "document", caption: Optional[str] = None
    ) -> Optional[Dict]:
        """Send a media message (PDF, image, etc.) via WhatsApp."""
        if not self._is_configured():
            return None
        
        media_key = "document" if media_type == "document" else "image"
        media_payload = {"link": media_url}
        if caption:
            media_payload["caption"] = caption
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": media_key,
            media_key: media_payload
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return {"status": "sent"}
                else:
                    logger.error(f"WhatsApp media error: {response.status_code}")
                    return {"status": "failed", "error": response.text}
                    
        except Exception as e:
            logger.error(f"WhatsApp media error: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    async def send_bulk_messages(self, recipients: List[str], message: str) -> List[Dict]:
        """Send messages to multiple recipients."""
        results = []
        for recipient in recipients:
            result = await self.send_message(recipient, message)
            results.append({"recipient": recipient, "result": result})
        return results
    
    async def test_connection(self) -> bool:
        """Test WhatsApp API connection."""
        if not self._is_configured():
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/{self.phone_number_id}",
                    headers=self.headers,
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception:
            return False
    
    def _is_configured(self) -> bool:
        """Check if WhatsApp API is configured."""
        return bool(self.phone_number_id and self.access_token)

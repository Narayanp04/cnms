"""ConnectXperts NMS - Email Alert Service"""
import logging
from typing import Optional, Dict, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending alert notifications."""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
    
    async def send_email(
        self, to: str, subject: str, body: str, 
        html_body: Optional[str] = None
    ) -> Optional[Dict]:
        """Send an email notification."""
        if not self._is_configured():
            logger.warning("Email not configured. Set SMTP settings.")
            return None
        
        try:
            message = MIMEMultipart("alternative")
            message["From"] = self.from_email
            message["To"] = to
            message["Subject"] = subject
            
            # Plain text version
            message.attach(MIMEText(body, "plain"))
            
            # HTML version (if provided)
            if html_body:
                message.attach(MIMEText(html_body, "html"))
            
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=self.smtp_port == 465
            ) as smtp:
                if self.smtp_port == 587:
                    await smtp.starttls()
                
                if self.smtp_user and self.smtp_password:
                    await smtp.login(self.smtp_user, self.smtp_password)
                
                await smtp.send_message(message)
                
            logger.info(f"Email sent to {to}: {subject}")
            return {"status": "sent", "recipient": to}
            
        except Exception as e:
            logger.error(f"Email error sending to {to}: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    async def send_bulk_emails(
        self, recipients: List[str], subject: str, body: str
    ) -> List[Dict]:
        """Send emails to multiple recipients."""
        results = []
        for recipient in recipients:
            result = await self.send_email(recipient, subject, body)
            results.append({"recipient": recipient, "result": result})
        return results
    
    def _is_configured(self) -> bool:
        """Check if email is configured."""
        return bool(self.smtp_host and self.from_email)

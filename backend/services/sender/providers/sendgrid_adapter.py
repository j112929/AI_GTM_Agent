import os
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from backend.utils.logger import setup_logger

logger = setup_logger("SendGridAdapter")

class SendGridEmailProvider:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "test@example.com")
        
        if self.api_key:
            self.sg = sendgrid.SendGridAPIClient(api_key=self.api_key)
        else:
            self.sg = None
            logger.warning("SENDGRID_API_KEY not set. Using Mock mode.")

    def send_email(self, to_email: str, subject: str, content: str) -> str:
        if not self.sg:
            logger.info(f"[Mock SendGrid] Sending to {to_email} | Subject: {subject}")
            return f"mock_sg_{to_email}"

        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=content
            )
            # Add custom arguments to help tracking
            message.custom_args = {"source": "ai_gtm_agent"}
            
            response = self.sg.send(message)
            
            # SendGrid response headers usually contain a message-id-like X-Message-Id
            # But the logic usually relies on the fact it succeeded.
            # We can use the header or generate a reliable ID.
            provider_id = response.headers.get('X-Message-Id', f"sg_success_{to_email}")
            
            logger.info(f"SendGrid sent email to {to_email}. Status: {response.status_code}")
            return provider_id
            
        except Exception as e:
            logger.error(f"SendGrid Error: {str(e)}")
            raise e

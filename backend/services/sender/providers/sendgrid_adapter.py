from datetime import datetime

class SendGridEmailProvider:
    """
    Demo implementation of a hypothetical Email Provider (SendGrid/Mailgun)
    """
    def __init__(self, api_key):
        self.api_key = api_key
        
    def send_email(self, to_email: str, subject: str, content: str) -> str:
        # In real code: requests.post('https://api.sendgrid.com/v3/mail/send', headers=..., json=...)
        print(f"[SendGrid Provider] Sending to {to_email} via API...")
        return f"sg_msg_id_{int(datetime.now().timestamp())}"

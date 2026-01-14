import os
import requests
from backend.storage.models import Reply
from backend.utils.logger import setup_logger

logger = setup_logger("Notifier")

class NotifierService:
    def __init__(self):
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    def notify_slack(self, message: str):
        if not self.slack_webhook_url:
            logger.info(f"[SLACK MOCK]: {message}")
            return

        try:
            payload = {"text": message}
            requests.post(self.slack_webhook_url, json=payload, timeout=5)
            logger.info("Sent notification to Slack.")
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")

    def handle_new_reply(self, reply: Reply):
        if reply.classification == "interested":
            self.notify_slack(f"🔥 HOT LEAD: New positive reply from Lead {reply.lead_id}!")
        else:
            self.notify_slack(f"New reply from Lead {reply.lead_id}: {reply.classification}")

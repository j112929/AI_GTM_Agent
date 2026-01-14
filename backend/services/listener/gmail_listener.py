from datetime import datetime
from typing import List
from backend.storage.models import Reply
from backend.storage.db import LeadStore
from backend.utils.logger import setup_logger

logger = setup_logger("InboxListener")

class InboxListener:
    def __init__(self, db: LeadStore):
        self.db = db

    def check_for_replies(self):
        logger.info("Checking inbox for new replies...")
        return []

    def simulate_incoming_reply(self, lead_id: str, content: str):
        logger.info(f"Detected reply from lead {lead_id}")
        return Reply(
            lead_id=lead_id,
            received_at=datetime.now(),
            content=content,
            classification="unknown" 
        )

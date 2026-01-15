import time
from datetime import datetime
from backend.storage.db import LeadStore
from backend.utils.logger import setup_logger

logger = setup_logger("RiskController")

class RiskController:
    """
    Handles Sending Risk Management: Caps, Throttling, and Blacklists.
    """
    def __init__(self, db: LeadStore):
        self.db = db
        # Config (Simulated env vars)
        self.DAILY_SEND_CAP = 50
        self.MIN_SECONDS_BETWEEN_SENDS = 5 
        
        self.last_send_time = 0

    def can_send(self, lead_id: str) -> bool:
        # 1. Check Global Cap
        metrics = self.db.get_todays_metrics()
        if metrics.sent_count >= self.DAILY_SEND_CAP:
            logger.warning(f"RiskControl: Daily Cap Reached ({metrics.sent_count}/{self.DAILY_SEND_CAP})")
            return False

        # 2. Check Throttling
        current_time = time.time()
        if current_time - self.last_send_time < self.MIN_SECONDS_BETWEEN_SENDS:
            logger.warning(f"RiskControl: Throttling active. Wait.")
            return False
            
        # 3. Check Lead Status (Redundant safety check)
        lead = self.db.get_lead(lead_id)
        if lead and "stopped" in lead.status:
            logger.warning(f"RiskControl: Lead {lead_id} is in stopped state: {lead.status}")
            return False

        return True

    def record_send_success(self):
        self.last_send_time = time.time()
        self.db.increment_metric("sent_count")

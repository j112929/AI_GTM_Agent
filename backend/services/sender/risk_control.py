import time
import re
from datetime import datetime
from backend.storage.db import LeadStore
from backend.utils.logger import setup_logger

logger = setup_logger("RiskController")

class RiskController:
    """
    Handles Sending Risk Management: Caps, Throttling, and Blacklists.
    Now Campaign-aware.
    """
    def __init__(self, db: LeadStore):
        self.db = db
        self.MIN_SECONDS_BETWEEN_SENDS = 5 
        self.last_send_time = 0

    def can_send(self, lead_id: str) -> bool:
        lead = self.db.get_lead(lead_id)
        if not lead:
            return False

        # 0. Check Lead Status
        if "stopped" in lead.status:
            logger.warning(f"RiskControl: Lead {lead_id} is in stopped state: {lead.status}")
            return False

        # Get Campaign Config
        campaign = self.db.get_campaign(lead.campaign_id)
        if not campaign:
             # Default Fallback if no campaign found or default
             campaign_limit = 50
             blacklist = []
        else:
             campaign_limit = campaign.daily_limit
             blacklist = campaign.blacklist_domains

        # 1. Check Global/Campaign Cap
        metrics = self.db.get_todays_metrics()
        if metrics.sent_count >= campaign_limit:
            logger.warning(f"RiskControl: Daily Cap Reached ({metrics.sent_count}/{campaign_limit})")
            return False

        # 2. Check Throttling
        current_time = time.time()
        if current_time - self.last_send_time < self.MIN_SECONDS_BETWEEN_SENDS:
            logger.warning(f"RiskControl: Throttling active. Wait.")
            return False
            
        # 3. Check Blacklist
        if lead.email:
            domain = lead.email.split('@')[-1].lower()
            for blocked_domain in blacklist:
                if blocked_domain.lower() in domain:
                    logger.warning(f"RiskControl: Domain {domain} is blacklisted.")
                    self.db.log_event(lead_id, "SEND_BLOCKED", f"Blacklisted domain: {domain}")
                    # Auto stop
                    self.db.update_lead_status(lead_id, "stopped_blacklist")
                    return False
        
        return True

    def record_send_success(self):
        self.last_send_time = time.time()
        self.db.increment_metric("sent_count")

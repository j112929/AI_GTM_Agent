from backend.storage.models import Reply
from backend.storage.db import LeadStore
from backend.core.llm_client import LLMClient
from backend.utils.logger import setup_logger

logger = setup_logger("ReplyClassifierAgent")

class ReplyClassifierAgent:
    def __init__(self, db: LeadStore):
        self.db = db
        self.llm = LLMClient()

    def classify_reply(self, reply: Reply):
        logger.info(f"Classifying reply from lead {reply.lead_id}...")
        
        # 1. Classification
        prompt = f"Classify this email reply: '{reply.content}'. Categories: interested, not_interested, out_of_office, bounce, unsubscribe, maybe."
        classification = self.llm.generate(prompt).strip().lower()
            
        reply.classification = classification
        logger.info(f"Reply classified as: {classification}")
        
        # 2. State Machine Transition (Stop Followups)
        # Any reply (except maybe OOO soft bounce) should likely stop the sequence.
        # But definitively: Interested, Not Interest, Bounce, Unsub -> STOP.
        
        new_status = f"replied_{classification}"
        
        if "bounce" in classification:
            new_status = "stopped_bounce"
            self.db.increment_metric("bounce_count")
        elif "unsubscribe" in classification or "remove" in classification:
            new_status = "stopped_unsub"
        elif "interested" in classification:
            self.db.increment_metric("positive_count")
            self.db.increment_metric("reply_count")
        else:
             self.db.increment_metric("reply_count")
        
        # Update DB
        self.db.update_lead_status(reply.lead_id, new_status)
        logger.info(f"Lead {reply.lead_id} status updated to {new_status} (Follow-ups Stopped)")
            
        return reply

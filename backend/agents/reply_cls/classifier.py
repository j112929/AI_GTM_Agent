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
        
        prompt = f"Classify this email reply: '{reply.content}'. Categories: interested, not_interested, out_of_office, maybe."
        classification = self.llm.generate(prompt).strip().lower()
            
        reply.classification = classification
        logger.info(f"Reply classified as: {classification}")
        
        # Update Lead status based on reply
        if "interested" in classification:
            self.db.update_lead_status(reply.lead_id, "replied_interested")
        elif "not_interested" in classification:
            self.db.update_lead_status(reply.lead_id, "replied_stop")
        else:
            self.db.update_lead_status(reply.lead_id, "replied_other")
            
        return reply

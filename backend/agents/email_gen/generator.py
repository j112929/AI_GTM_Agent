import json
from backend.storage.models import Lead
from backend.core.llm_client import LLMClient
from backend.utils.logger import setup_logger
from backend.storage.db import LeadStore

logger = setup_logger("EmailGeneratorAgent")

class EmailGeneratorAgent:
    def __init__(self, db: LeadStore = None):
        self.llm = LLMClient()
        self.db = db

    def generate_email(self, lead: Lead):
        logger.info(f"Generating email for lead: {lead.id}")
        
        prompt = f"""
        Draft a cold email to {lead.name} at {lead.company_name}.
        Context: {lead.company_summary}
        Our Value: {lead.product_summary}
        
        Output strictly valid JSON with keys: 'subject', 'body'.
        """
        
        try:
            generated_text = self.llm.generate(prompt, system_prompt="You are a world-class Copywriter.")
            # Cleanup
            cleaned_text = generated_text.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(cleaned_text)
            
            lead.generated_email_subject = data.get("subject", "Connecting")
            lead.generated_email_body = data.get("body", "Hi, I'd like to connect.")
            lead.status = "processed" 
            
            if self.db: self.db.log_event(lead.id, "GEN_OK", "Email Draft Prepared")
            logger.info(f"Email generated for {lead.id}")
            
        except json.JSONDecodeError:
            # Fallback
            logger.warning(f"Email Gen JSON Parse Fail {lead.id}. Using fallback.")
            lead.generated_email_subject = f"Question for {lead.name}"
            lead.generated_email_body = f"Hi {lead.name}, I reviewed {lead.company_name} and think we can help."
            lead.status = "processed"
            if self.db: self.db.log_event(lead.id, "GEN_WARN", "JSON Parse Failed, used Template Fallback")
            
        except Exception as e:
            logger.error(f"Email Gen Error: {e}")
            if self.db: self.db.log_event(lead.id, "GEN_ERR", str(e))
            # Don't change status to processed if critical error? 
            # Allow fallback if possible, else fail.
            
        return lead

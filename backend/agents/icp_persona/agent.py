from typing import Dict
import json
from backend.storage.models import Lead
from backend.core.llm_client import LLMClient
from backend.utils.logger import setup_logger
from backend.storage.db import LeadStore

logger = setup_logger("ICPPersonaAgent")

class ICPPersonaAgent:
    def __init__(self, db: LeadStore = None):
        self.llm = LLMClient()
        self.db = db # Pass DB to log events

    def analyze_lead(self, lead: Lead):
        logger.info(f"Analyzing lead: {lead.id} ({lead.company_name})")
        
        prompt = (f"Analyze the company '{lead.company_name}' for fit with 'AI GTM Agent'. "
                  f"Output strictly valid JSON with keys: 'company_summary', 'product_summary', 'fit_score'. "
                  f"No markdown.")
        
        try:
            response_text = self.llm.generate(prompt)
            # Cleanup
            cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(cleaned_text)
            lead.company_summary = data.get("company_summary", response_text)
            lead.product_summary = data.get("product_summary", "Auto-generated")
            lead.status = "enriched"
            
            if self.db: 
                self.db.log_event(lead.id, "ENRICH_OK", "Analysis Successful")
                
        except json.JSONDecodeError:
             logger.warning(f"ICP Parse Fail {lead.id}. Using fallback.")
             lead.company_summary = response_text
             lead.product_summary = "Fallback summary"
             lead.status = "enriched"
             if self.db: self.db.log_event(lead.id, "ENRICH_WARN", "JSON Parse Failed")
             
        except Exception as e:
             logger.error(f"ICP Error: {e}")
             if self.db: self.db.log_event(lead.id, "ENRICH_ERR", str(e))
             lead.status = "new" # Do not progress
             
        logger.info(f"Lead enriched: {lead.id}")
        return lead

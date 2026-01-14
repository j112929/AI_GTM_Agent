from typing import Dict
from backend.storage.models import Lead
from backend.core.llm_client import LLMClient
from backend.utils.logger import setup_logger

logger = setup_logger("ICPPersonaAgent")

class ICPPersonaAgent:
    def __init__(self):
        self.llm = LLMClient()

    def run_llm_analysis(self, company_name: str, product_info: str) -> Dict[str, str]:
        prompt = f"Analyze the company '{company_name}' and explain how it fits our product '{product_info}'. Return a summary."
        analysis_text = self.llm.generate(prompt, system_prompt="You are an expert Sales Researcher.")
        
        # In a real system, we'd force JSON output or parse it.
        # For now, we split the mock response or just use the whole text.
        return {
            "company_summary": analysis_text,
            "product_summary": "High alignment detected based on company tech stack." # Mock enrichment
        }

    def process_lead(self, lead: Lead):
        logger.info(f"Analyzing lead: {lead.id} ({lead.company_name})")
        
        analysis = self.run_llm_analysis(lead.company_name, "Our AI GTM Product")
        
        lead.company_summary = analysis["company_summary"]
        lead.product_summary = analysis["product_summary"]
        lead.status = "enriched"
        
        logger.info(f"Lead enriched: {lead.id}")
        return lead

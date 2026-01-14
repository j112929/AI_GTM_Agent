from backend.storage.models import Lead
from backend.core.llm_client import LLMClient
from backend.utils.logger import setup_logger

logger = setup_logger("EmailGeneratorAgent")

class EmailGeneratorAgent:
    def __init__(self):
        self.llm = LLMClient()

    def generate_email(self, lead: Lead):
        logger.info(f"Generating email for lead: {lead.id}")
        
        prompt = f"""
        Draft a cold email to {lead.name} at {lead.company_name}.
        Context: {lead.company_summary}
        Our Value: {lead.product_summary}
        """
        
        generated_text = self.llm.generate(prompt, system_prompt="You are a world-class Copywriter.")
        
        # Simple parsing of the mock response
        lines = generated_text.split("\n", 1)
        subject = lines[0].replace("Subject:", "").strip() if len(lines) > 0 else "Hello"
        body = lines[1].strip() if len(lines) > 1 else generated_text
        
        lead.generated_email_subject = subject
        lead.generated_email_body = body
        lead.status = "processed" 
        
        logger.info(f"Email generated for {lead.id}")
        return lead

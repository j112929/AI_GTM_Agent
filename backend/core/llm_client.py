import time
from typing import Optional
from backend.core.config import config
from backend.utils.logger import setup_logger

logger = setup_logger("LLMClient")

class LLMClient:
    def __init__(self):
        self.mock_mode = config.MOCK_LLM

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if self.mock_mode:
            logger.info(f"MOCK LLM Request: {prompt[:50]}...")
            return self._mock_response(prompt)
        
        # Real implementation would go here (e.g., call OpenAI)
        logger.warning("Real LLM call not implemented yet, using mock.")
        return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> str:
        time.sleep(0.5) # Simulate latency
        prompt_lower = prompt.lower()
        
        if "analyze" in prompt_lower or "summary" in prompt_lower:
            return "Analyzed Company: A leader in cloud infrastructure. Strong fit for our DevOps tools aimed at reducing latency."
        
        if "email" in prompt_lower or "subject" in prompt_lower:
            return "Subject: Optimization for your Cloud Infrastructure\n\nHi [Name],\n\nI saw your work on cloud infra..."
            
        if "classify" in prompt_lower:
            if "interested" in prompt_lower:
                return "interested"
            if "stop" in prompt_lower:
                return "not_interested"
            return "maybe"
            
        return "Mock LLM Response"

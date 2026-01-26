import os
from typing import Optional
from backend.core.config import config
from backend.utils.logger import setup_logger

logger = setup_logger("LLMClient")

class LLMClient:
    def __init__(self):
        self.mock_mode = config.MOCK_LLM
        self.api_key = config.OPENAI_API_KEY
        
        if not self.mock_mode and self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                
                # LangSmith Integration
                if config.LANGCHAIN_TRACING_V2:
                    try:
                        from langsmith.wrappers import wrap_openai
                        self.client = wrap_openai(self.client)
                        logger.info("LangSmith tracing enabled.")
                    except ImportError:
                        logger.warning("LangSmith not installed, skipping tracing.")
                    except Exception as e:
                        logger.warning(f"Failed to enable LangSmith tracing: {e}")
                
                # Langfuse Integration
                if config.LANGFUSE_PUBLIC_KEY and config.LANGFUSE_SECRET_KEY:
                    try:
                        from langfuse.openai import OpenAI as LangfuseOpenAI
                        # Re-initialize client with Langfuse wrapper if keys are present
                        # Note: If both LangSmith and Langfuse are active, we might need a different approach 
                        # but Langfuse's wrapper inherits from OpenAI, so it should be fine to re-instantiate 
                        # or we can wrap the existing client if possible. 
                        # The cleanest way for Langfuse is to use their class directly.
                        self.client = LangfuseOpenAI(api_key=self.api_key)
                        logger.info("Langfuse tracing enabled.")
                    except ImportError:
                        logger.warning("Langfuse not installed, skipping tracing.")
                    except Exception as e:
                         logger.warning(f"Failed to enable Langfuse tracing: {e}")

                logger.info("OpenAI Client initialized.")
            except ImportError:
                logger.error("openai module not found. Install it with `pip install openai`")
                self.mock_mode = True
        else:
            if not self.mock_mode:
                logger.warning("OPENAI_API_KEY not set. Falling back to Mock mode.")
            self.mock_mode = True

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if self.mock_mode:
            return self._mock_response(prompt)
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model="gpt-4o", # Or gpt-3.5-turbo
                messages=messages,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API Error: {e}. Falling back to mock.")
            return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> str:
        # time.sleep(0.5) # Commented out to speed up demo
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

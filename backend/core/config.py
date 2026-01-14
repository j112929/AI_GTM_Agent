import os

class Config:
    DB_PATH = os.getenv("DB_PATH", "gtm_agent.db")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    MOCK_LLM = os.getenv("MOCK_LLM", "True").lower() == "true"
    
config = Config()

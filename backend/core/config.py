import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_PATH = os.getenv("DB_PATH", "gtm_agent.db")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    MOCK_LLM = os.getenv("MOCK_LLM", "True").lower() == "true"
    
    # LangSmith Configuration
    LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "AI_GTM_Agent")
    
config = Config()

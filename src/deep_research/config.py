import os
from dotenv import load_dotenv
from deep_research.models import Config

def load_config() -> Config:
    """Loads configuration from environment variables."""
    load_dotenv()
    
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
    if not tavily_api_key:
        raise ValueError("TAVILY_API_KEY environment variable is not set.")
        
    return Config(
        gemini_api_key=gemini_api_key,
        tavily_api_key=tavily_api_key
    )

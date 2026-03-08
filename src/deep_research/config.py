import os
from dotenv import load_dotenv
from deep_research.models import Config

def load_config() -> Config:
    """Loads configuration from environment variables."""
    load_dotenv()
    
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    gemini_rpm = int(os.getenv("GEMINI_RPM", "15"))
    max_chars_per_page = int(os.getenv("MAX_CHARS_PER_PAGE", "8000"))
    max_concurrent_fetches = int(os.getenv("MAX_CONCURRENT_FETCHES", "5"))
    fetch_timeout = int(os.getenv("FETCH_TIMEOUT", "10"))
    
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
    if not tavily_api_key:
        raise ValueError("TAVILY_API_KEY environment variable is not set.")
        
    return Config(
        gemini_api_key=gemini_api_key,
        tavily_api_key=tavily_api_key,
        gemini_model=gemini_model,
        gemini_rpm=gemini_rpm,
        max_chars_per_page=max_chars_per_page,
        max_concurrent_fetches=max_concurrent_fetches,
        fetch_timeout=fetch_timeout
    )

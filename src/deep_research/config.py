import os
from dotenv import load_dotenv
from deep_research.models import Config

def load_config(max_searches: int = None, max_depth: int = None) -> Config:
    """Loads configuration from environment variables with optional overrides."""
    load_dotenv()
    
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    gemini_rpm = int(os.getenv("GEMINI_RPM", "15"))
    max_chars_per_page = int(os.getenv("MAX_CHARS_PER_PAGE", "8000"))
    max_concurrent_fetches = int(os.getenv("MAX_CONCURRENT_FETCHES", "5"))
    fetch_timeout = int(os.getenv("FETCH_TIMEOUT", "10"))
    
    # Defaults if not provided via env or argument
    default_max_searches = int(os.getenv("MAX_SEARCHES", "30"))
    default_max_depth = int(os.getenv("MAX_DEPTH", "2"))
    
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
        fetch_timeout=fetch_timeout,
        max_searches=max_searches if max_searches is not None else default_max_searches,
        max_depth=max_depth if max_depth is not None else default_max_depth
    )

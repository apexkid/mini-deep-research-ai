import os
from dotenv import load_dotenv
from deep_research.models import Config


def load_config(
    model: str = "gemini-2.5-flash",
    planner_model: str = None,
    extractor_model: str = None,
    gap_analyzer_model: str = None,
    synthesizer_model: str = None,
    rpm: int = 15,
    max_chars: int = 8000,
    concurrent: int = 5,
    timeout: int = 10,
    searches: int = 30,
    depth: int = 2,
) -> Config:
    """
    Loads configuration. 
    API keys are read from environment variables. 
    Other settings are passed in (typically from CLI flags).
    """
    load_dotenv()

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    tavily_api_key = os.getenv("TAVILY_API_KEY")

    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
    if not tavily_api_key:
        raise ValueError("TAVILY_API_KEY environment variable is not set.")

    return Config(
        gemini_api_key=gemini_api_key,
        tavily_api_key=tavily_api_key,
        gemini_model=model,
        planner_model=planner_model or model,
        extractor_model=extractor_model or model,
        gap_analyzer_model=gap_analyzer_model or model,
        synthesizer_model=synthesizer_model or model,
        gemini_rpm=rpm,
        max_chars_per_page=max_chars,
        max_concurrent_fetches=concurrent,
        fetch_timeout=timeout,
        max_searches=searches,
        max_depth=depth,
    )

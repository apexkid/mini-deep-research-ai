import aiohttp
import logging
from typing import List
from deep_research.models import SearchResult

logger = logging.getLogger(__name__)

async def search_tavily(query: str, api_key: str, max_results: int = 5) -> List[SearchResult]:
    """
    Searches Tavily for the given query.
    """
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "include_answer": False,
        "include_images": False,
        "include_raw_content": False,
        "max_results": max_results
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.warning(f"Tavily API returned status {response.status}: {error_text}")
                return []
            
            data = await response.json()
            results = data.get("results", [])
            
            search_results = []
            for r in results:
                search_results.append(SearchResult(
                    url=r.get("url", ""),
                    title=r.get("title", ""),
                    content=r.get("content", ""),
                    score=r.get("score", 0.0)
                ))
            
            return search_results

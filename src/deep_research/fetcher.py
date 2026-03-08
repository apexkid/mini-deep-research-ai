import asyncio
import aiohttp
import trafilatura
import logging
from typing import List, Optional
from deep_research.models import PageContent, Config

logger = logging.getLogger(__name__)

async def fetch_page(url: str, session: aiohttp.ClientSession, timeout: int) -> Optional[PageContent]:
    """
    Fetches a single page and extracts its content.
    """
    try:
        async with session.get(url, timeout=timeout) as response:
            if response.status != 200:
                logger.warning(f"Failed to fetch {url}: Status {response.status}")
                return None
            
            html = await response.text()
            extracted_text = trafilatura.extract(html)
            
            if not extracted_text:
                logger.warning(f"No content extracted from {url}")
                return None
            
            metadata = trafilatura.extract_metadata(html)
            title = metadata.title if metadata else None
            
            return PageContent(url=url, text=extracted_text, title=title)
            
    except asyncio.TimeoutError:
        logger.warning(f"Timeout fetching {url}")
        return None
    except Exception as e:
        logger.warning(f"Error fetching {url}: {str(e)}")
        return None

async def fetch_pages_concurrently(urls: List[str], config: Config) -> List[PageContent]:
    """
    Fetches multiple pages concurrently with a limit on concurrency.
    """
    semaphore = asyncio.Semaphore(config.max_concurrent_fetches)
    
    async def sem_fetch(url: str, session: aiohttp.ClientSession):
        async with semaphore:
            return await fetch_page(url, session, config.fetch_timeout)
            
    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as session:
        tasks = [sem_fetch(url, session) for url in urls]
        results = await asyncio.gather(*tasks)
        
    return [r for r in results if r is not None]

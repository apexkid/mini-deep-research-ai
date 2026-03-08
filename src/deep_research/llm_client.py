import logging
import asyncio
import time
from typing import Type, TypeVar, Optional, Any
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from deep_research.models import Config

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class RateLimiter:
    """
    A simple async rate limiter to restrict requests per minute.
    """
    def __init__(self, rpm: int):
        self.interval = 60.0 / rpm
        self.last_call = 0.0
        self.lock = asyncio.Lock()

    async def wait(self):
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_call
            if elapsed < self.interval:
                sleep_time = self.interval - elapsed
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
            self.last_call = time.time()

class GeminiClient:
    """
    Wrapper for the Google GenAI SDK with proactive rate limiting.
    """
    def __init__(self, config: Config):
        self.client = genai.Client(api_key=config.gemini_api_key)
        self.model_name = config.gemini_model
        self.limiter = RateLimiter(config.gemini_rpm)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ClientError),
    )
    async def generate_content(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        config: Optional[types.GenerateContentConfig] = None
    ) -> str:
        """
        Generates raw text content with rate limiting.
        """
        await self.limiter.wait()
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    **(config.model_dump() if config else {})
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Error generating content with Gemini ({self.model_name}): {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ClientError),
    )
    async def generate_structured(
        self, 
        prompt: str, 
        response_model: Type[T],
        system_instruction: Optional[str] = None,
    ) -> T:
        """
        Generates structured content validated against a Pydantic model with rate limiting.
        """
        await self.limiter.wait()
        try:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=response_model,
            )
            
            # Note: The SDK currently might have issues with some model types and JSON mode
            # If errors occur, we might need more specific handling here.
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            
            return response.parsed
        except Exception as e:
            logger.error(f"Error generating structured content with Gemini ({self.model_name}): {str(e)}")
            raise

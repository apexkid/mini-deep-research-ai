import logging
import asyncio
import time
import os
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
from dotenv import load_dotenv
from deep_research.models import Config
from langfuse import observe, get_client

# Ensure environment variables are loaded before Langfuse SDK initializes
load_dotenv()

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

    @observe(as_type="generation")
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ClientError),
    )
    async def generate_content(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        config: Optional[types.GenerateContentConfig] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Generates raw text content with rate limiting.
        """
        current_model = model or self.model_name
        langfuse = get_client()
        langfuse.update_current_generation(
            name="gemini_generate_content",
            model=current_model,
            input=[
                {"role": "system", "content": system_instruction} if system_instruction else None,
                {"role": "user", "content": prompt}
            ]
        )
        await self.limiter.wait()
        try:
            response = await self.client.aio.models.generate_content(
                model=current_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    **(config.model_dump() if config else {})
                )
            )
            langfuse.update_current_generation(output=response.text)
            return response.text
        except Exception as e:
            logger.error(f"Error generating content with Gemini ({current_model}): {str(e)}")
            raise

    @observe(as_type="generation")
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
        temperature: Optional[float] = None,
        model: Optional[str] = None
    ) -> T:
        """
        Generates structured content validated against a Pydantic model with rate limiting.
        """
        current_model = model or self.model_name
        langfuse = get_client()
        langfuse.update_current_generation(
            name="gemini_generate_structured",
            model=current_model,
            input=[
                {"role": "system", "content": system_instruction} if system_instruction else None,
                {"role": "user", "content": prompt}
            ],
            model_parameters={"temperature": temperature} if temperature is not None else {}
        )
        await self.limiter.wait()
        try:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=response_model,
                temperature=temperature,
            )
            
            response = await self.client.aio.models.generate_content(
                model=current_model,
                contents=prompt,
                config=config
            )
            
            output_val = response.parsed.model_dump() if hasattr(response.parsed, "model_dump") else response.parsed
            langfuse.update_current_generation(output=output_val)
            return response.parsed
        except Exception as e:
            logger.error(f"Error generating structured content with Gemini ({current_model}): {str(e)}")
            raise

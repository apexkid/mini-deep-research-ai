import logging
from typing import List
from deep_research.models import PageContent, Finding, FindingList, Config
from deep_research.llm_client import GeminiClient
from google.genai import types

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """
You are a senior research extraction agent. Your goal is to extract high-quality, 
factual findings from web page content based on a research question.

Rules for Findings:
1. Specificity is Mandatory: A good finding contains specific data, numbers, 
   dates, or names. Avoid vague claims like "the market is growing." 
   Instead, use "The vertical farming market grew by 20% in 2024 to $3.2B."
2. Evidence: Every finding must include a direct supporting detail or 
   statistic from the text.
3. Factual Accuracy: Do not invent, extrapolate, or combine information 
   beyond what is explicitly stated in the provided text.
4. Confidence: 
   - "high": Authoritative source with specific, verifiable data.
   - "medium": Plausible claim from a reliable source, but perhaps less detailed.
   - "low": Vague, potentially outdated, or from a less certain source.
5. Penalize Redundancy: Do not extract the same fact multiple times in 
   different ways.

Examples:
- GOOD: "Average energy costs for vertical farms range from $8 to $12 per 
  square foot annually [Source: AgFunder 2023]."
- BAD: "Vertical farms have high electricity bills because of the lights."
- GOOD: "AeroFarms raised $100M in Series E funding led by Ingka Group 
  in July 2019."
- BAD: "Many vertical farming companies are receiving investment from 
  large corporations."
"""

EXTRACTION_USER_PROMPT = """
Research question: {query}

Page title: {title}
Page URL: {url}
Page content:
---
{text}
---

Extract 0-5 high-quality, specific findings relevant to the research question.
"""

class Extractor:
    def __init__(self, client: GeminiClient, config: Config):
        self.client = client
        self.config = config

    async def extract_findings(self, query: str, page: PageContent) -> List[Finding]:
        """
        Extracts findings from a page given a research query.
        Uses a low temperature (0.2) for high factual consistency.
        """
        # Truncate content based on config
        max_chars = self.config.max_chars_per_page
        truncated_text = page.text[:max_chars]
        if len(page.text) > max_chars:
            truncated_text += f"\n\n[Content truncated due to length (max {max_chars} chars)...]"

        prompt = EXTRACTION_USER_PROMPT.format(
            query=query,
            title=page.title or "Untitled",
            url=page.url,
            text=truncated_text
        )
        
        try:
            # We add temperature to the call via GenerateContentConfig
            # Note: GeminiClient.generate_structured uses types.GenerateContentConfig internally
            # but we need to pass it through. Let's update GeminiClient first.
            
            result = await self.client.generate_structured(
                prompt=prompt,
                response_model=FindingList,
                system_instruction=EXTRACTION_SYSTEM_PROMPT,
                temperature=0.2 # We will update the client to handle this
            )
            
            # Manually attach URL to findings
            findings = []
            if result and result.findings:
                for f in result.findings:
                    f_dict = f.model_dump()
                    f_dict['url'] = page.url
                    findings.append(Finding(**f_dict))
                
            return findings
        except Exception as e:
            logger.error(f"Error during extraction from {page.url}: {str(e)}")
            return []

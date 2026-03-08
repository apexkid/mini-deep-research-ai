import logging
from typing import List
from deep_research.models import PageContent, Finding, FindingList, Config
from deep_research.llm_client import GeminiClient

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """
You are a research extraction agent. Given the text content of a web page
and a specific research question, extract key findings.

Rules:
- Extract 0-5 findings. Each finding must be a specific, factual claim.
- Include supporting evidence (a key data point, statistic, or detail).
- Assign confidence: "high" if the source is authoritative and the data is
  specific, "medium" if plausible but from a secondary source, "low" if
  vague or potentially outdated.
- If the page is irrelevant to the research question, return an empty list.
- Do NOT invent or extrapolate. Only extract what is explicitly stated.
"""

EXTRACTION_USER_PROMPT = """
Research question: {query}

Page title: {title}
Page URL: {url}
Page content:
---
{text}
---

Extract findings relevant to the research question.
"""


class Extractor:
    def __init__(self, client: GeminiClient, config: Config):
        self.client = client
        self.config = config

    async def extract_findings(self, query: str, page: PageContent) -> List[Finding]:
        """
        Extracts findings from a page given a research query.
        """
        # Truncate content based on config
        max_chars = self.config.max_chars_per_page
        truncated_text = page.text[:max_chars]
        if len(page.text) > max_chars:
            truncated_text += (
                f"\n\n[Content truncated due to length (max {max_chars} chars)...]"
            )

        prompt = EXTRACTION_USER_PROMPT.format(
            query=query,
            title=page.title or "Untitled",
            url=page.url,
            text=truncated_text,
        )

        try:
            result = await self.client.generate_structured(
                prompt=prompt,
                response_model=FindingList,
                system_instruction=EXTRACTION_SYSTEM_PROMPT,
            )

            # Manually attach URL to findings as the LLM doesn't do it
            findings = []
            for f in result.findings:
                f_dict = f.model_dump()
                f_dict["url"] = page.url
                findings.append(Finding(**f_dict))

            return findings
        except Exception as e:
            logger.error(f"Error during extraction from {page.url}: {str(e)}")
            return []

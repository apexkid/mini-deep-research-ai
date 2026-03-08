import logging
from typing import List
from deep_research.models import Finding, GapAnalysis, Config
from deep_research.llm_client import GeminiClient

logger = logging.getLogger(__name__)

GAP_ANALYSIS_SYSTEM_PROMPT = """
You are a research gap analysis agent. Your goal is to review the findings extracted 
so far for a specific sub-question and determine if there are significant gaps 
that need to be filled.

Rules:
- If the findings sufficiently answer the sub-question, set is_satisfied to True.
- If there are missing details, conflicting information, or a lack of specific data 
  (e.g., missing 2025 forecasts or specific cost numbers), set is_satisfied to False.
- If not satisfied, provide 1-3 highly specific search queries to fill the gaps.
- Provide a brief explanation of what is missing.
"""

GAP_ANALYSIS_USER_PROMPT = """
Sub-question: {question}

Current Findings:
{findings_text}

Analyze the gaps and determine if more research is needed.
"""

class GapAnalyzer:
    def __init__(self, client: GeminiClient, config: Config):
        self.client = client
        self.config = config

    async def analyze_gaps(self, question: str, findings: List[Finding]) -> GapAnalysis:
        """
        Analyzes findings for a sub-question and identifies knowledge gaps.
        """
        findings_text = "\n".join([f"- {f.claim} (Evidence: {f.evidence})" for f in findings])
        
        prompt = GAP_ANALYSIS_USER_PROMPT.format(
            question=question,
            findings_text=findings_text if findings_text else "No findings yet."
        )
        
        try:
            analysis = await self.client.generate_structured(
                prompt=prompt,
                response_model=GapAnalysis,
                system_instruction=GAP_ANALYSIS_SYSTEM_PROMPT,
                model=self.config.gap_analyzer_model
            )
            return analysis
        except Exception as e:
            logger.error(f"Error during gap analysis: {str(e)}")
            # Fallback to satisfied to avoid infinite loops on error
            return GapAnalysis(is_satisfied=True, follow_up_queries=[], explanation=f"Error: {str(e)}")

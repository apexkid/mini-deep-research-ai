import logging
from typing import List
from deep_research.models import Finding, ResearchReport
from deep_research.llm_client import GeminiClient

logger = logging.getLogger(__name__)

SYNTHESIS_SYSTEM_PROMPT = """
You are a senior research synthesizer. Your goal is to take a set of extracted findings
and a research question, and write a comprehensive, well-structured Markdown report.

Guidelines:
- If a 'Note' about research being cut short is provided in the prompt, you MUST include it at the very beginning of your report (before the Executive Summary).
- Start with a high-level executive summary.
- Organize the report into logical sections based on the findings.
- Use numbered citations [n] that match the provided sources.
- Be objective, factual, and concise.
- Use Markdown formatting (headers, bullet points, bold text).
- Include a 'Sources' section at the very end with the numbered list of URLs.
"""

SYNTHESIS_USER_PROMPT = """
Research Question: {query}

Findings:
{findings_text}

Sources:
{sources_text}

{budget_note}

Write the research report now.
"""

class Synthesizer:
    def __init__(self, client: GeminiClient):
        self.client = client

    async def synthesize_report(self, query: str, findings: List[Finding], budget_exhausted: bool = False) -> str:
        """
        Synthesizes a final Markdown report from extracted findings.
        """
        # Prepare findings text with source attribution
        findings_lines = []
        unique_sources = []
        
        # Helper to get source index
        def get_source_idx(url: str):
            if url not in unique_sources:
                unique_sources.append(url)
            return unique_sources.index(url) + 1

        for f in findings:
            idx = get_source_idx(f.url if hasattr(f, 'url') else "Unknown")
            findings_lines.append(f"- {f.claim} (Evidence: {f.evidence}) [{idx}]")
            
        findings_text = "\n".join(findings_lines)
        sources_text = "\n".join([f"{i}. {url}" for i, url in enumerate(unique_sources, 1)])

        budget_note = ""
        if budget_exhausted:
            budget_note = "Note: research was cut short due to search budget limits. Some sub-questions may be incompletely covered."

        prompt = SYNTHESIS_USER_PROMPT.format(
            query=query,
            findings_text=findings_text,
            sources_text=sources_text,
            budget_note=budget_note
        )
        
        try:
            report_text = await self.client.generate_content(
                prompt=prompt,
                system_instruction=SYNTHESIS_SYSTEM_PROMPT
            )
            return report_text
        except Exception as e:
            logger.error(f"Error during report synthesis: {str(e)}")
            return f"# Research Report: {query}\n\nError during synthesis: {str(e)}"

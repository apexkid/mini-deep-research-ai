import logging
from deep_research.models import ResearchPlan, SubQuestion
from deep_research.llm_client import GeminiClient

logger = logging.getLogger(__name__)

PLANNING_SYSTEM_PROMPT = """
You are a research planning agent. Your goal is to decompose a complex research question
into 3-7 smaller, more focused sub-questions.

Rules:
- For each sub-question, provide 2-3 specific search queries.
- Assign a priority (high, medium, low) to each sub-question.
- Ensure the sub-questions cover different aspects of the main query to provide a comprehensive answer.
- Focus on factual, data-driven sub-questions.
"""

PLANNING_USER_PROMPT = """
Research Question: {query}

Decompose this into a structured research plan.
"""


class Planner:
    def __init__(self, client: GeminiClient):
        self.client = client

    async def create_plan(self, query: str) -> ResearchPlan:
        """
        Decomposes a query into a structured ResearchPlan.
        """
        prompt = PLANNING_USER_PROMPT.format(query=query)

        try:
            plan = await self.client.generate_structured(
                prompt=prompt,
                response_model=ResearchPlan,
                system_instruction=PLANNING_SYSTEM_PROMPT,
            )
            return plan
        except Exception as e:
            logger.error(f"Error during planning: {str(e)}")
            # Fallback to a single sub-question if planning fails
            return ResearchPlan(
                sub_questions=[
                    SubQuestion(question=query, queries=[query], priority="high")
                ]
            )

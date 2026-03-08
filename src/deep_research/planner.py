import logging
from deep_research.models import ResearchPlan, SubQuestion, Config
from deep_research.llm_client import GeminiClient

logger = logging.getLogger(__name__)

PLANNING_SYSTEM_PROMPT = """
You are an expert research planner. Decompose the user's complex research query into a logical sequence of 1 to 5 focused sub-questions. 

Your goal is maximum research coverage (MECE: Mutually Exclusive, Collectively Exhaustive).

RULES:
1. Sequence the questions logically (e.g., foundational context first, specific data/analysis later).
2. Provide exactly 2 highly targeted search queries per sub-question.
3. Assign a priority (High, Medium, Low) to each sub-question based on its importance to the core query.
4. Focus strictly on factual, verifiable, data-driven aspects. Do not generate broad or philosophical sub-questions.
"""

PLANNING_USER_PROMPT = """
Research Question: {query}

Decompose this into a structured research plan.
"""

class Planner:
    def __init__(self, client: GeminiClient, config: Config):
        self.client = client
        self.config = config

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
                model=self.config.planner_model,
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

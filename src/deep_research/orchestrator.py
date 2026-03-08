import os
import logging
from datetime import datetime
from typing import Set, List
from rich.console import Console
from deep_research.models import Config, ResearchPlan, Finding, SubQuestion
from deep_research.searcher import search_tavily
from deep_research.fetcher import fetch_pages_concurrently
from deep_research.llm_client import GeminiClient
from deep_research.extractor import Extractor
from deep_research.synthesizer import Synthesizer
from deep_research.planner import Planner

logger = logging.getLogger(__name__)
console = Console()


class Orchestrator:
    def __init__(self, config: Config):
        self.config = config
        self.client = GeminiClient(config)
        self.extractor = Extractor(self.client, config)
        self.synthesizer = Synthesizer(self.client)
        self.planner = Planner(self.client)
        self.visited_urls: Set[str] = set()

    def _sort_sub_questions(
        self, sub_questions: List[SubQuestion]
    ) -> List[SubQuestion]:
        """Sorts sub-questions by priority: High (0) > Medium (1) > Low (2)."""
        priority_map = {"high": 0, "medium": 1, "low": 2}
        return sorted(
            sub_questions, key=lambda sq: priority_map.get(sq.priority.lower(), 3)
        )

    async def run(self, query: str):
        """
        Runs the full research pipeline.
        """
        # --- PLANNING STEP ---
        console.print(f"[bold green][PLAN][/bold green] Decomposing query: {query}")
        plan = await self.planner.create_plan(query)

        if not plan.sub_questions:
            console.print("[red]No sub-questions generated. Aborting.[/red]")
            return

        sorted_sqs = self._sort_sub_questions(plan.sub_questions)

        console.print(
            f"[bold green][PLAN][/bold green] Decomposed into {len(sorted_sqs)} sub-questions (ordered by priority):"
        )
        for i, sq in enumerate(sorted_sqs, 1):
            console.print(f"  {i}. [{sq.priority.upper()}] {sq.question}")

        all_findings: List[Finding] = []

        # --- SEQUENTIAL RESEARCH LOOP ---
        for i, sq in enumerate(sorted_sqs, 1):
            console.print(
                f"\n[bold blue][STEP {i}/{len(sorted_sqs)}][/bold blue] Researching: {sq.question}"
            )

            sq_findings: List[Finding] = []

            for search_query in sq.queries:
                console.print(f"  [dim]Searching: {search_query}[/dim]")
                search_results = await search_tavily(
                    search_query, self.config.tavily_api_key
                )

                if not search_results:
                    continue

                # Filter out already visited URLs
                new_results = [
                    r for r in search_results if r.url not in self.visited_urls
                ]
                if not new_results:
                    console.print("  [dim]No new URLs found in this search.[/dim]")
                    continue

                # --- FETCH STEP ---
                # Limit to config.max_concurrent_fetches per search query
                top_urls = [
                    res.url for res in new_results[: self.config.max_concurrent_fetches]
                ]
                console.print(f"  [dim]Fetching {len(top_urls)} new pages...[/dim]")

                pages = await fetch_pages_concurrently(top_urls, self.config)

                # Mark as visited
                for url in top_urls:
                    self.visited_urls.add(url)

                # --- EXTRACTION STEP ---
                for page in pages:
                    console.print(f"  [dim]Extracting from {page.url[:50]}...[/dim]")
                    findings = await self.extractor.extract_findings(sq.question, page)
                    sq_findings.extend(findings)

            console.print(
                f"  [cyan]Sub-question complete: {len(sq_findings)} findings.[/cyan]"
            )
            all_findings.extend(sq_findings)

        if not all_findings:
            console.print(
                "[yellow]No findings extracted from any sub-question.[/yellow]"
            )
            return

        console.print(
            f"\n[bold cyan]Final Synthesis: {len(all_findings)} findings from {len(self.visited_urls)} sources.[/bold cyan]"
        )

        # --- SYNTHESIS STEP ---
        console.print(f"[bold green]Synthesizing final report...[/bold green]")
        report_md = await self.synthesizer.synthesize_report(query, all_findings)

        # --- OUTPUT STEP ---
        os.makedirs("output", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = (
            "".join(x for x in query if x.isalnum() or x in " -_")[:50]
            .strip()
            .replace(" ", "_")
        )
        filename = f"output/report_{safe_query}_{timestamp}.md"

        with open(filename, "w") as f:
            f.write(report_md)

        console.print(f"\n[bold green][DONE][/bold green] Research complete!")
        console.print(f"Report saved to: [bold cyan]{filename}[/bold cyan]")

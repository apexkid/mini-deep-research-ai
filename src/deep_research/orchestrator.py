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
from deep_research.gap_analyzer import GapAnalyzer

logger = logging.getLogger(__name__)
console = Console()

class Orchestrator:
    def __init__(self, config: Config):
        self.config = config
        self.client = GeminiClient(config)
        self.extractor = Extractor(self.client, config)
        self.synthesizer = Synthesizer(self.client)
        self.planner = Planner(self.client)
        self.gap_analyzer = GapAnalyzer(self.client)
        self.visited_urls: Set[str] = set()
        self.search_count = 0
        self.budget_exhausted = False

    def _sort_sub_questions(self, sub_questions: List[SubQuestion]) -> List[SubQuestion]:
        """Sorts sub-questions by priority: High (0) > Medium (1) > Low (2)."""
        priority_map = {"high": 0, "medium": 1, "low": 2}
        return sorted(sub_questions, key=lambda sq: priority_map.get(sq.priority.lower(), 3))

    def _is_duplicate(self, new_finding: Finding, existing_findings: List[Finding], threshold: float = 0.7) -> bool:
        """
        Checks if a finding is a duplicate of any existing findings.
        Uses a simple Jaccard similarity on characters for speed.
        """
        new_claim = new_finding.claim.lower()
        
        for existing in existing_findings:
            existing_claim = existing.claim.lower()
            
            # Substring check (one is inside the other)
            if new_claim in existing_claim or existing_claim in new_claim:
                return True
            
            # Simple character overlap check
            set1 = set(new_claim)
            set2 = set(existing_claim)
            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))
            similarity = intersection / union if union > 0 else 0
            
            if similarity > threshold:
                return True
                
        return False

    async def _research_queries(self, question: str, queries: List[str], existing_findings: List[Finding]) -> List[Finding]:
        """Runs the search-fetch-extract cycle for a list of queries."""
        new_findings: List[Finding] = []
        
        for search_query in queries:
            if self.search_count >= self.config.max_searches:
                if not self.budget_exhausted:
                    console.print(f"\n[bold red][BUDGET][/bold red] {self.search_count}/{self.config.max_searches} searches used, stopping research.")
                    self.budget_exhausted = True
                return new_findings

            self.search_count += 1
            console.print(f"  [dim]Searching ({self.search_count}/{self.config.max_searches}): {search_query}[/dim]")
            
            search_results = await search_tavily(search_query, self.config.tavily_api_key)
            
            if not search_results:
                continue

            # Filter out already visited URLs
            new_results = [r for r in search_results if r.url not in self.visited_urls]
            if not new_results:
                console.print("  [dim]No new URLs found in this search.[/dim]")
                continue

            # --- FETCH STEP ---
            top_urls = [res.url for res in new_results[:self.config.max_concurrent_fetches]]
            console.print(f"  [dim]Fetching {len(top_urls)} new pages...[/dim]")
            
            pages = await fetch_pages_concurrently(top_urls, self.config)
            
            # Mark as visited
            for url in top_urls:
                self.visited_urls.add(url)
            
            # --- EXTRACTION STEP ---
            for page in pages:
                console.print(f"  [dim]Extracting from {page.url[:50]}...[/dim]")
                extractor_findings = await self.extractor.extract_findings(question, page)
                
                # Deduplicate before adding
                for f in extractor_findings:
                    if not self._is_duplicate(f, existing_findings + new_findings):
                        new_findings.append(f)
                    else:
                        logger.debug(f"Skipping duplicate finding: {f.claim[:50]}...")
                
        return new_findings

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
        
        console.print(f"[bold green][PLAN][/bold green] Decomposed into {len(sorted_sqs)} sub-questions (ordered by priority):")
        for i, sq in enumerate(sorted_sqs, 1):
            console.print(f"  {i}. [{sq.priority.upper()}] {sq.question}")

        all_findings: List[Finding] = []
        
        # --- SEQUENTIAL RESEARCH LOOP ---
        for i, sq in enumerate(sorted_sqs, 1):
            if self.budget_exhausted:
                break

            console.print(f"\n[bold blue][STEP {i}/{len(sorted_sqs)}][/bold blue] Researching: {sq.question}")
            
            # Initial research for the sub-question
            sq_findings = await self._research_queries(sq.question, sq.queries, all_findings)
            
            # --- GAP ANALYSIS & FOLLOW-UP LOOP ---
            current_depth = 1
            while current_depth < self.config.max_depth and not self.budget_exhausted:
                console.print(f"  [bold yellow][GAP][/bold yellow] Analyzing results (depth {current_depth}) for: {sq.question}")
                gap_analysis = await self.gap_analyzer.analyze_gaps(sq.question, sq_findings)
                
                if gap_analysis.is_satisfied or not gap_analysis.follow_up_queries:
                    console.print(f"  [bold green][GAP][/bold green] Sub-question satisfied.")
                    break
                
                console.print(f"  [bold yellow][GAP][/bold yellow] Missing: {gap_analysis.explanation}")
                console.print(f"  [bold yellow][GAP][/bold yellow] Running follow-up research with {len(gap_analysis.follow_up_queries)} queries...")
                
                follow_up_findings = await self._research_queries(sq.question, gap_analysis.follow_up_queries, all_findings + sq_findings)
                sq_findings.extend(follow_up_findings)
                console.print(f"  [cyan]Follow-up complete: {len(follow_up_findings)} new findings.[/cyan]")
                current_depth += 1

            console.print(f"  [cyan]Sub-question complete: {len(sq_findings)} total findings.[/cyan]")
            all_findings.extend(sq_findings)

        if not all_findings:
            console.print("[yellow]No findings extracted from any sub-question.[/yellow]")
            return
            
        console.print(f"\n[bold cyan]Final Synthesis: {len(all_findings)} unique findings from {len(self.visited_urls)} sources.[/bold cyan]")
        if self.budget_exhausted:
            console.print("[bold red][BUDGET] Note: Research was cut short due to budget limits.[/bold red]")
        
        # --- SYNTHESIS STEP ---
        console.print(f"[bold green]Synthesizing final report...[/bold green]")
        report_md = await self.synthesizer.synthesize_report(query, all_findings, budget_exhausted=self.budget_exhausted)
        
        # --- OUTPUT STEP ---
        os.makedirs("output", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = "".join(x for x in query if x.isalnum() or x in " -_")[:50].strip().replace(" ", "_")
        filename = f"output/report_{safe_query}_{timestamp}.md"
        
        with open(filename, "w") as f:
            f.write(report_md)
            
        console.print(f"\n[bold green][DONE][/bold green] Research complete!")
        console.print(f"Report saved to: [bold cyan]{filename}[/bold cyan]")

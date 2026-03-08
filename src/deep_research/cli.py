import click
import asyncio
import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from deep_research.config import load_config
from deep_research.searcher import search_tavily
from deep_research.fetcher import fetch_pages_concurrently
from deep_research.llm_client import GeminiClient
from deep_research.extractor import Extractor
from deep_research.synthesizer import Synthesizer

console = Console()

async def run_research(query: str):
    """Orchestrates the research process."""
    try:
        config = load_config()
        client = GeminiClient(config)
        extractor = Extractor(client, config)
        synthesizer = Synthesizer(client)
        
        # --- SEARCH STEP ---
        console.print(f"[bold green]Searching for:[/bold green] {query}")
        search_results = await search_tavily(query, config.tavily_api_key)
        
        if not search_results:
            console.print("[yellow]No search results found.[/yellow]")
            return

        console.print(f"[bold cyan]Found {len(search_results)} results.[/bold cyan]")
        
        # --- FETCH STEP ---
        top_urls = [res.url for res in search_results[:config.max_concurrent_fetches]]
        console.print(f"[bold green]Fetching top {len(top_urls)} pages...[/bold green]")
        pages = await fetch_pages_concurrently(top_urls, config)
        
        if not pages:
            console.print("[yellow]No content extracted from any page.[/yellow]")
            return

        console.print(f"[bold cyan]Successfully fetched {len(pages)} pages.[/bold cyan]")
        
        # --- EXTRACTION STEP ---
        console.print(f"[bold green]Extracting findings with {config.gemini_model}...[/bold green]")
        all_findings = []
        for page in pages:
            console.print(f"[dim]Extracting from {page.title or page.url}...[/dim]")
            findings = await extractor.extract_findings(query, page)
            all_findings.extend(findings)
            
        if not all_findings:
            console.print("[yellow]No findings extracted.[/yellow]")
            return
            
        console.print(f"[bold cyan]Total: {len(all_findings)} findings extracted.[/bold cyan]")
        
        # --- SYNTHESIS STEP ---
        console.print(f"[bold green]Synthesizing report...[/bold green]")
        report_md = await synthesizer.synthesize_report(query, all_findings)
        
        # --- OUTPUT STEP ---
        os.makedirs("output", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = "".join(x for x in query if x.isalnum() or x in " -_")[:50].strip().replace(" ", "_")
        filename = f"output/report_{safe_query}_{timestamp}.md"
        
        with open(filename, "w") as f:
            f.write(report_md)
            
        console.print(f"\n[bold green]Research complete![/bold green]")
        console.print(f"Report saved to: [bold cyan]{filename}[/bold cyan]")
        
    except Exception as e:
        console.print(f"[bold red]Error during research:[/bold red] {str(e)}")
        raise

@click.command()
@click.argument('query')
def main(query: str):
    """Deep Research Agent CLI."""
    try:
        asyncio.run(run_research(query))
    except Exception:
        exit(1)

if __name__ == "__main__":
    main()

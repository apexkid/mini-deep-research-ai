import click
import asyncio
from rich.console import Console
from rich.table import Table
from deep_research.config import load_config
from deep_research.searcher import search_tavily
from deep_research.fetcher import fetch_pages_concurrently

console = Console()

async def run_search(query: str):
    """Orchestrates the research process."""
    try:
        config = load_config()
        
        # --- SEARCH STEP ---
        console.print(f"[bold green]Searching for:[/bold green] {query}")
        search_results = await search_tavily(query, config.tavily_api_key)
        
        if not search_results:
            console.print("[yellow]No search results found.[/yellow]")
            return

        console.print(f"[bold cyan]Found {len(search_results)} results.[/bold cyan]")
        
        # --- FETCH STEP ---
        # Take the top 5 results for fetching
        top_urls = [res.url for res in search_results[:5]]
        console.print(f"[bold green]Fetching top {len(top_urls)} pages...[/bold green]")
        
        pages = await fetch_pages_concurrently(top_urls)
        
        if not pages:
            console.print("[yellow]No content extracted from any page.[/yellow]")
            return

        console.print(f"[bold cyan]Successfully fetched and extracted {len(pages)} pages.[/bold cyan]")
        
        # --- DISPLAY SUMMARY ---
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=2)
        table.add_column("Source", width=30)
        table.add_column("Snippet (First 500 chars)")
        
        for i, page in enumerate(pages, 1):
            snippet = (page.text[:500] + "...") if len(page.text) > 500 else page.text
            # Use domain or title for Source
            source = page.title or page.url.split("//")[-1].split("/")[0]
            table.add_row(str(i), source, snippet)
            
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Error during research:[/bold red] {str(e)}")
        raise

@click.command()
@click.argument('query')
def main(query: str):
    """Deep Research Agent CLI."""
    try:
        asyncio.run(run_search(query))
    except Exception:
        exit(1)

if __name__ == "__main__":
    main()

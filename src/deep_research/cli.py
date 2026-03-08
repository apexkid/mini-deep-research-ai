import click
import asyncio
from rich.console import Console
from rich.table import Table
from deep_research.config import load_config
from deep_research.searcher import search_tavily

console = Console()

async def run_search(query: str):
    """Orchestrates the search process."""
    try:
        config = load_config()
        console.print(f"[bold green]Searching for:[/bold green] {query}")
        
        results = await search_tavily(query, config.tavily_api_key)
        
        if not results:
            console.print("[yellow]No results found.[/yellow]")
            return

        console.print(f"[bold cyan]Found {len(results)} results:[/bold cyan]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=2)
        table.add_column("Title")
        table.add_column("URL")
        
        for i, res in enumerate(results, 1):
            table.add_row(str(i), res.title, res.url)
            
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Error during search:[/bold red] {str(e)}")
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

import click
import asyncio
from dotenv import load_dotenv

# Ensure environment variables are loaded as early as possible
load_dotenv()

from rich.console import Console
from deep_research.config import load_config
from deep_research.orchestrator import Orchestrator
from langfuse import get_client

console = Console()

async def run_pipeline(query: str, searches: int, depth: int):
    """Entry point for the research pipeline."""
    try:
        config = load_config(max_searches=searches, max_depth=depth)
        orchestrator = Orchestrator(config)
        await orchestrator.run(query)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        # import traceback
        # traceback.print_exc()
        raise

@click.command()
@click.argument('query')
@click.option('--searches', default=None, type=int, help='Maximum number of searches allowed.')
@click.option('--depth', default=None, type=int, help='Maximum depth of research (iterations per sub-question).')
def main(query: str, searches: int, depth: int):
    """Deep Research Agent CLI."""
    try:
        asyncio.run(run_pipeline(query, searches, depth))
        get_client().flush()
    except Exception:
        get_client().flush()
        exit(1)

if __name__ == "__main__":
    main()

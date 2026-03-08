import click
import asyncio
from rich.console import Console
from deep_research.config import load_config
from deep_research.orchestrator import Orchestrator

console = Console()

async def run_pipeline(query: str):
    """Entry point for the research pipeline."""
    try:
        config = load_config()
        orchestrator = Orchestrator(config)
        await orchestrator.run(query)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        import traceback
        # Only show traceback if needed for debugging
        # traceback.print_exc()
        raise

@click.command()
@click.argument('query')
def main(query: str):
    """Deep Research Agent CLI."""
    try:
        asyncio.run(run_pipeline(query))
    except Exception:
        exit(1)

if __name__ == "__main__":
    main()

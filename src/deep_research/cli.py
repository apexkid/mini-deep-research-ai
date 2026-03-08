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

async def run_pipeline(query: str, **kwargs):
    """Entry point for the research pipeline."""
    try:
        config = load_config(**kwargs)
        orchestrator = Orchestrator(config)
        await orchestrator.run(query)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise

@click.command()
@click.argument('query')
@click.option('--model', default="gemini-2.5-flash", help='Default Gemini model to use.')
@click.option('--planner-model', help='Model override for the planning step.')
@click.option('--extractor-model', help='Model override for the extraction step.')
@click.option('--gap-analyzer-model', help='Model override for the gap analysis step.')
@click.option('--synthesizer-model', help='Model override for the synthesis step.')
@click.option('--rpm', default=15, type=int, help='Gemini API requests per minute limit.')
@click.option('--max-chars', default=8000, type=int, help='Maximum characters to extract per page.')
@click.option('--concurrent', default=5, type=int, help='Maximum concurrent page fetches.')
@click.option('--timeout', default=10, type=int, help='Timeout in seconds for page fetches.')
@click.option('--searches', default=30, type=int, help='Maximum number of searches allowed.')
@click.option('--depth', default=2, type=int, help='Maximum depth of research (iterations per sub-question).')
def main(query: str, **kwargs):
    """Deep Research Agent CLI."""
    try:
        asyncio.run(run_pipeline(query, **kwargs))
        get_client().flush()
    except Exception:
        get_client().flush()
        exit(1)

if __name__ == "__main__":
    main()

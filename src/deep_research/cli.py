import click
from rich.console import Console
from deep_research.config import load_config

console = Console()

@click.command()
@click.argument('query')
def main(query: str):
    """Deep Research Agent CLI."""
    try:
        # For now, just load the config and print the starting message
        config = load_config()
        console.print(f"[bold green]Starting research on:[/bold green] {query}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()

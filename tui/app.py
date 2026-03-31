import sys
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table

from tui.client import KGClient
from django_lightrag.schemas import IngestRequest, SearchRequest, GraphRAGRequest

console = Console()
client = KGClient()

def ingest_menu():
    text = Prompt.ask("Enter text to ingest")
    source_id = Prompt.ask("Enter source ID (e.g. url or title)", default="manual-input")
    with console.status("[bold green]Ingesting and extracting knowledge...") as status:
        try:
            res = client.ingest(IngestRequest(text=text, source_id=source_id))
            console.print(Panel(f"[bold green]Success![/]\nExtracted {res.concepts_extracted} concepts and {res.relations_extracted} relations.\nStatus: {res.status}", title="Ingestion Result"))
        except Exception as e:
            console.print(f"[bold red]Error:[/] {e}")

def search_menu():
    query = Prompt.ask("Enter search query")
    with console.status("[bold blue]Searching...") as status:
        try:
            res = client.search(SearchRequest(query=query))
            table = Table(title=f"Search Results for '{query}'")
            table.add_column("Score", justify="right", style="cyan", no_wrap=True)
            table.add_column("Pref Label", style="magenta")
            table.add_column("Definition", style="green")
            
            for c in res.concepts:
                table.add_row(f"{c.confidence_score:.2f}", c.pref_label, c.definition[:100] + "...")
            console.print(table)
        except Exception as e:
            console.print(f"[bold red]Error:[/] {e}")

def graphrag_menu():
    query = Prompt.ask("Enter your question")
    with console.status("[bold magenta]GraphRAG reasoning in progress...") as status:
        try:
            res = client.graphrag(GraphRAGRequest(natural_language_query=query))
            console.print(Panel(res.answer, title="GraphRAG Answer", border_style="magenta"))
            console.print("\n[bold]Grounding concepts used:[/bold]")
            for c in res.grounding_concepts:
                console.print(f" - [cyan]{c.pref_label}[/]: {c.definition[:60]}...")
        except Exception as e:
            console.print(f"[bold red]Error:[/] {e}")

def validate_menu():
    with console.status("[bold yellow]Validating graph...") as status:
        try:
            res = client.validate()
            color = "green" if res.is_valid else "red"
            txt = f"Graph Valid: {res.is_valid}\nIsolated Concepts: {len(res.isolated_concepts)}\nCircular Hierarchies: {len(res.circular_hierarchies)}\nDuplicate Labels: {len(res.duplicate_labels)}"
            console.print(Panel(txt, title="Graph Validation", border_style=color))
        except Exception as e:
            console.print(f"[bold red]Error:[/] {e}")

def main():
    while True:
        console.print("\n[bold]Research Knowledge Graph TUI[/bold]")
        console.print("1. Ingest Text")
        console.print("2. Search Concepts")
        console.print("3. GraphRAG Query")
        console.print("4. Validate Graph")
        console.print("5. Exit")
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5"])
        
        if choice == "1":
            ingest_menu()
        elif choice == "2":
            search_menu()
        elif choice == "3":
            graphrag_menu()
        elif choice == "4":
            validate_menu()
        elif choice == "5":
            sys.exit(0)

if __name__ == "__main__":
    main()

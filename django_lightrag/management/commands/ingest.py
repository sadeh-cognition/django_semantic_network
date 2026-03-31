import djclick as click
from django_lightrag.core import ingest_text_chunk


@click.command()
@click.option(
    "--file", required=True, type=click.Path(exists=True), help="Path to text file"
)
@click.option("--source-id", required=True, help="Identifier for the source")
def command(file, source_id):
    """Ingests a text file into the knowledge graph."""
    click.echo(f"Reading {file}...")
    with open(file, "r", encoding="utf-8") as f:
        text = f.read()

    click.echo("Starting ingestion (LLM Extraction + Graph update)...")
    try:
        log = ingest_text_chunk(text=text, source_id=source_id)

        if log.status == "success":
            click.secho(
                f"Success! Extracted {log.concepts_extracted} concepts and {log.relations_extracted} relations.",
                fg="green",
            )
        else:
            click.secho(f"Ingestion failed: {log.error_message}", fg="red")
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")

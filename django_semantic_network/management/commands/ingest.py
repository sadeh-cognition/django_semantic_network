import djclick as click
from django_semantic_network.core import ingest_text_chunk


@click.command()
@click.option("--text", required=True, help="Text to ingest")
@click.option("--source-id", required=True, help="Identifier for the source")
def command(text, source_id):
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

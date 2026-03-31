import djclick as click
from tui.client import KGClient
from django_lightrag.schemas import IngestRequest


@click.command()
def command():
    """Seeds the DB with AI/ML domain data."""
    click.echo("Seeding DB...")

    seed_texts = [
        "Machine learning is a subfield of artificial intelligence. Deep learning is a specialized area of machine learning based on artificial neural networks.",
        "Natural language processing (NLP) is a branch of AI that helps computers understand, interpret and manipulate human language.",
        "Large language models (LLMs) like GPT-4 are a type of deep learning model designed to understand and generate human-like text.",
        "Artificial neural networks are computing systems inspired by the biological neural networks that constitute animal brains. They are the foundation of deep learning.",
    ]

    try:
        client = KGClient()
        for i, text in enumerate(seed_texts):
            click.echo(f"Ingesting seed chunk {i + 1}/{len(seed_texts)}...")
            res = client.ingest(
                IngestRequest(
                    text=text,
                    source_id=f"seed-{i + 1}",
                )
            )
            if res.status == "success":
                click.secho(
                    f"  + Extracted {res.concepts_extracted} concepts", fg="green"
                )
            else:
                click.secho(f"  - Failed: {res.status}", fg="red")

        click.secho("Seeding complete.", fg="green")
    except Exception as e:
        click.secho(f"Seeding error: {e}. Is the server running?", fg="red")

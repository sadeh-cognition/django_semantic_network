import djclick as click
from django_semantic_network.storage import init_ladybug_schema


@click.command()
def command():
    """Initializes the LadybugDB graph schema."""
    click.echo("Initializing LadybugDB schema...")
    try:
        init_ladybug_schema()
        click.secho("Schema initialized successfully.", fg="green")
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")

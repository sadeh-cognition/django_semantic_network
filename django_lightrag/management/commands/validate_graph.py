import djclick as click
from django_lightrag.storage import get_ladybug_connection
from django_lightrag.graph_builder import (
    validate_no_circular_hierarchy,
    validate_no_isolated_concepts,
    validate_no_duplicates,
)


@click.command()
def command():
    """Validates the knowledge graph for inconsistencies."""
    conn = get_ladybug_connection()
    click.echo("Running validations...")

    isolated = validate_no_isolated_concepts(conn)
    circular = validate_no_circular_hierarchy(conn)
    dups = validate_no_duplicates(conn)

    if isolated:
        click.secho(f"Found {len(isolated)} isolated concepts.", fg="yellow")
    if circular:
        click.secho(f"Found {len(circular)} circular hierarchies.", fg="red")
    if dups:
        click.secho(f"Found {len(dups)} duplicate prefLabels.", fg="red")

    if not isolated and not circular and not dups:
        click.secho("Graph is valid. No issues found.", fg="green")

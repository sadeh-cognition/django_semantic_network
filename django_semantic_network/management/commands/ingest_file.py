from pathlib import Path

import djclick as click

from .ingest import run_ingest


def _chunk_to_text(chunk) -> str:
    if isinstance(chunk, str):
        return chunk

    text = getattr(chunk, "text", None)
    if isinstance(text, str):
        return text

    raise click.ClickException("SemanticChunker returned a chunk without text.")


def chunk_file(
    file_path: Path,
    *,
    chunk_size: int,
    threshold: float,
    encoding: str,
) -> list[str]:
    from chonkie import SemanticChunker

    text = file_path.read_text(encoding=encoding).strip()
    if not text:
        raise click.ClickException(f"File '{file_path}' is empty.")

    chunker = SemanticChunker(chunk_size=chunk_size, threshold=threshold)
    chunks = chunker.chunk(text)
    chunk_texts = [_chunk_to_text(chunk).strip() for chunk in chunks]
    chunk_texts = [chunk_text for chunk_text in chunk_texts if chunk_text]

    if not chunk_texts:
        raise click.ClickException(
            f"SemanticChunker did not produce any chunks for '{file_path}'."
        )

    return chunk_texts


@click.command()
@click.argument(
    "file_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--source-id",
    help="Base source identifier. Defaults to the resolved file path.",
)
@click.option("--chunk-size", default=2048, show_default=True, type=int)
@click.option("--threshold", default=0.8, show_default=True, type=float)
@click.option("--encoding", default="utf-8", show_default=True)
def command(
    file_path: Path,
    source_id: str | None,
    chunk_size: int,
    threshold: float,
    encoding: str,
):
    """Chunk a file with SemanticChunker and ingest each chunk."""
    chunk_texts = chunk_file(
        file_path,
        chunk_size=chunk_size,
        threshold=threshold,
        encoding=encoding,
    )
    base_source_id = source_id or str(file_path.resolve())

    click.echo(f"Chunked '{file_path}' into {len(chunk_texts)} chunks.")

    success_count = 0
    for index, chunk_text in enumerate(chunk_texts, start=1):
        chunk_source_id = f"{base_source_id}::chunk-{index}"
        click.echo(f"Ingesting chunk {index}/{len(chunk_texts)} as '{chunk_source_id}'")
        log = run_ingest(text=chunk_text, source_id=chunk_source_id, announce=False)
        if log.status == "success":
            success_count += 1

    color = "green" if success_count == len(chunk_texts) else "yellow"
    click.secho(
        f"Finished ingesting {success_count}/{len(chunk_texts)} chunks from '{file_path}'.",
        fg=color,
    )

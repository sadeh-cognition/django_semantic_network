import sys
from types import SimpleNamespace

import pytest

from django_semantic_network.management.commands import ingest_file


class FakeChunk:
    def __init__(self, text):
        self.text = text


class FakeSemanticChunker:
    def __init__(self, *, chunk_size, threshold):
        self.chunk_size = chunk_size
        self.threshold = threshold

    def chunk(self, text):
        assert text == "Alpha paragraph.\n\nBeta paragraph."
        return [FakeChunk("Alpha paragraph."), FakeChunk("Beta paragraph.")]


@pytest.mark.django_db
def test_ingest_file_command_chunks_and_ingests_each_chunk(tmp_path, monkeypatch):
    file_path = tmp_path / "notes.txt"
    file_path.write_text("Alpha paragraph.\n\nBeta paragraph.", encoding="utf-8")

    monkeypatch.setitem(
        sys.modules,
        "chonkie",
        SimpleNamespace(SemanticChunker=FakeSemanticChunker),
    )

    ingested = []

    def fake_run_ingest(*, text, source_id, announce):
        ingested.append((text, source_id, announce))
        return SimpleNamespace(status="success")

    monkeypatch.setattr(ingest_file, "run_ingest", fake_run_ingest)

    ingest_file.command.main(
        args=[str(file_path), "--source-id", "doc-123"],
        prog_name="ingest_file",
        standalone_mode=False,
    )

    assert ingested == [
        ("Alpha paragraph.", "doc-123::chunk-1", False),
        ("Beta paragraph.", "doc-123::chunk-2", False),
    ]

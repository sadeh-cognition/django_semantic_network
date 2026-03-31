import os

import pytest


@pytest.fixture(autouse=True)
def setup_env():
    # Ensure test environment uses Groq according to rules
    os.environ["LLM_MODEL"] = "groq/llama-3.1-8b-instant"


@pytest.fixture
def ninja_client():
    from ninja.testing import TestClient

    from django_semantic_network.urls import api

    return TestClient(api)


@pytest.fixture(autouse=True)
def isolated_storage(settings, tmp_path):
    from django_semantic_network import storage

    settings.LADYBUG_DB_PATH = str(tmp_path / "test_graph.lbug")
    settings.CHROMADB_PATH = tmp_path / "test_chroma"

    storage._lbug_db = None
    storage._lbug_conn = None
    storage._chroma_client = None

    yield

    storage._lbug_db = None
    storage._lbug_conn = None
    storage._chroma_client = None


@pytest.fixture(autouse=True)
def db_schema(isolated_storage):
    # Ensure each test starts with a fresh Ladybug schema and isolated vector store.
    from django_semantic_network.storage import init_ladybug_schema

    init_ladybug_schema()

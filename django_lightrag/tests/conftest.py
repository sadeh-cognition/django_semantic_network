import pytest
import os
from ninja.testing import TestClient
from django_lightrag.urls import api
from django_lightrag.storage import init_ladybug_schema

@pytest.fixture(autouse=True)
def setup_env():
    # Ensure test environment uses Groq according to rules
    os.environ["LLM_MODEL"] = "groq/llama-3.1-8b-instant"

@pytest.fixture
def ninja_client():
    return TestClient(api)

@pytest.fixture(autouse=True)
def db_schema():
    # Ensure Ladybug schema is created before tests
    init_ladybug_schema()

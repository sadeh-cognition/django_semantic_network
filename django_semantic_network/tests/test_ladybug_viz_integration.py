from pathlib import Path

from django.conf import settings
from django.urls import resolve, reverse

from django_semantic_network.ladybug_viz_proxy import resolve_ladybug_db_path


def test_ladybug_viz_root_url_is_mounted():
    path = reverse("ladybug_viz:database_overview", kwargs={"db_name": "research_kg"})

    assert path == "/ladybug-viz/research_kg/"
    assert resolve(path).namespace == "ladybug_viz"


def test_ladybug_viz_uses_configured_db_path():
    db_name = Path(settings.LADYBUG_DB_PATH).stem
    resolved = resolve_ladybug_db_path(db_name)

    assert resolved == str(Path(settings.LADYBUG_DB_PATH))

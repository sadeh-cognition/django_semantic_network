from django.urls import resolve, reverse


def test_ladybug_viz_root_url_is_mounted():
    path = reverse("ladybug_viz:database_overview", kwargs={"db_name": "research_kg"})

    assert path == "/ladybug-viz/research_kg/"
    assert resolve(path).namespace == "ladybug_viz"

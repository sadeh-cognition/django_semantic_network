from django.urls import resolve, reverse


def test_chromadb_viz_root_url_is_mounted():
    path = reverse("django_chromadb_viz:collection_list")

    assert path == "/chromadb/"
    assert resolve(path).namespace == "django_chromadb_viz"

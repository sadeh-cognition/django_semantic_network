from django.urls import path

from .ladybug_viz_proxy import (
    api,
    cypher_console,
    database_overview,
    graph_view,
    table_detail,
)

app_name = "ladybug_viz"

urlpatterns = [
    path("api/", api.urls),
    path("<str:db_name>/", database_overview, name="database_overview"),
    path(
        "<str:db_name>/table/<str:table_name>/",
        table_detail,
        name="table_detail",
    ),
    path("<str:db_name>/graph/", graph_view, name="graph_view"),
    path("<str:db_name>/cypher/", cypher_console, name="cypher_console"),
]

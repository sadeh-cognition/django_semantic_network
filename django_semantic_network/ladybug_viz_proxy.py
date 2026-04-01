from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from ninja import NinjaAPI, Router

from ladybug_viz import services
from ladybug_viz.schemas import (
    CypherRequestSchema,
    CypherResponseSchema,
    ErrorSchema,
    GraphDataSchema,
    PaginatedRowsSchema,
)


def resolve_ladybug_db_path(db_name: str) -> str:
    requested_name = Path(db_name).stem
    configured_path = Path(settings.LADYBUG_DB_PATH)

    if configured_path.stem == requested_name:
        return str(configured_path)

    return str(Path(settings.BASE_DIR) / f"{requested_name}.lbug")


def database_overview(request: HttpRequest, db_name: str) -> HttpResponse:
    db_path = resolve_ladybug_db_path(db_name)
    tables = services.list_tables(db_path)

    node_tables = [t for t in tables if t["type"] == "NODE"]
    rel_tables = [t for t in tables if t["type"] == "REL"]

    for nt in node_tables:
        nt["count"] = services.get_node_count(db_path, nt["name"])

    for rt in rel_tables:
        rt["count"] = services.get_rel_count(db_path, rt["name"])
        rt["connections"] = services.get_connection_info(db_path, rt["name"])

    return render(
        request,
        "ladybug_viz/database_overview.html",
        {
            "db_name": db_name,
            "node_tables": node_tables,
            "rel_tables": rel_tables,
            "total_node_tables": len(node_tables),
            "total_rel_tables": len(rel_tables),
        },
    )


def table_detail(request: HttpRequest, db_name: str, table_name: str) -> HttpResponse:
    db_path = resolve_ladybug_db_path(db_name)

    tables = services.list_tables(db_path)
    table_entry = next((t for t in tables if t["name"] == table_name), None)
    table_type = table_entry["type"] if table_entry else "NODE"

    columns = services.get_table_info(db_path, table_name)
    connections: list = []

    if table_type == "NODE":
        rows = services.get_node_rows(db_path, table_name, limit=50, offset=0)
        total = services.get_node_count(db_path, table_name)
    else:
        rows = services.get_rel_rows(db_path, table_name, limit=50, offset=0)
        total = services.get_rel_count(db_path, table_name)
        connections = services.get_connection_info(db_path, table_name)

    return render(
        request,
        "ladybug_viz/table_detail.html",
        {
            "db_name": db_name,
            "table_name": table_name,
            "table_type": table_type,
            "columns": columns,
            "rows": rows,
            "total_count": total,
            "connections": connections,
        },
    )


def graph_view(request: HttpRequest, db_name: str) -> HttpResponse:
    return render(request, "ladybug_viz/graph_view.html", {"db_name": db_name})


def cypher_console(request: HttpRequest, db_name: str) -> HttpResponse:
    return render(request, "ladybug_viz/cypher_console.html", {"db_name": db_name})


router = Router()


@router.get(
    "/{db_name}/tables/{table_name}/rows",
    response={200: PaginatedRowsSchema, 400: ErrorSchema},
)
def get_table_rows(
    request,  # noqa: ANN001
    db_name: str,
    table_name: str,
    limit: int = 50,
    offset: int = 0,
) -> tuple[int, PaginatedRowsSchema | ErrorSchema]:
    db_path = resolve_ladybug_db_path(db_name)
    try:
        tables = services.list_tables(db_path)
        table_entry = next((t for t in tables if t["name"] == table_name), None)
        if table_entry is None:
            return 400, ErrorSchema(detail=f"Table '{table_name}' not found")

        if table_entry["type"] == "NODE":
            rows = services.get_node_rows(db_path, table_name, limit, offset)
            total = services.get_node_count(db_path, table_name)
        else:
            rows = services.get_rel_rows(db_path, table_name, limit, offset)
            total = services.get_rel_count(db_path, table_name)

        return 200, PaginatedRowsSchema(
            rows=rows, total_count=total, limit=limit, offset=offset
        )
    except Exception as exc:
        return 400, ErrorSchema(detail=str(exc))


@router.post(
    "/{db_name}/cypher",
    response={200: CypherResponseSchema, 400: ErrorSchema},
)
def execute_cypher(
    request,  # noqa: ANN001
    db_name: str,
    payload: CypherRequestSchema,
) -> tuple[int, CypherResponseSchema | ErrorSchema]:
    db_path = resolve_ladybug_db_path(db_name)
    try:
        result = services.run_cypher(db_path, payload.query)
        return 200, CypherResponseSchema(**result)
    except Exception as exc:
        return 400, ErrorSchema(detail=str(exc))


@router.get(
    "/{db_name}/graph",
    response={200: GraphDataSchema, 400: ErrorSchema},
)
def get_graph_data(
    request,  # noqa: ANN001
    db_name: str,
    node_limit: int = 200,
) -> tuple[int, GraphDataSchema | ErrorSchema]:
    db_path = resolve_ladybug_db_path(db_name)
    try:
        data = services.get_graph_data(db_path, node_limit=node_limit)
        return 200, GraphDataSchema(**data)
    except Exception as exc:
        return 400, ErrorSchema(detail=str(exc))


api = NinjaAPI(urls_namespace="ladybug_viz_api", docs_url=None)
api.add_router("/", router)

import json
import re
from pathlib import Path

from render.placement.flow_page_placer_factory import build_flow_page_placer

from shared.flow_endpoints.endpoint_catalog import EndpointCatalog
from shared.flow_endpoints.endpoint_items import EndpointItem
from shared.flow_endpoints.endpoint_subgraph import EndpointSubgraph
from shared.models.flow_graph import FlowGraph


def endpoint_slug(entry_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", entry_id)


def _summary(item: EndpointItem) -> dict:
    return {
        "id": item.id,
        "label": item.label,
        "title": item.title,
        "one_liner": item.one_liner,
        "route_count": item.route_count,
        "file": item.file,
        "line": item.line,
    }


def write_repo_home_fixture(graph: FlowGraph, fixture_dir: Path) -> int:
    catalog = EndpointCatalog()
    subgraph = EndpointSubgraph()
    placer = build_flow_page_placer()
    items = catalog.items(graph)
    home = {
        "repo": graph.repo,
        "title": graph.repo,
        "description": graph.page_title,
        "endpoints": [_summary(i) for i in items if i.is_route],
        "entry_points": [_summary(i) for i in items if not i.is_route],
    }
    fixture_dir.mkdir(parents=True, exist_ok=True)
    (fixture_dir / "repo_home.json").write_text(json.dumps(home, indent=2), encoding="utf-8")
    endpoint_dir = fixture_dir / "endpoints"
    endpoint_dir.mkdir(parents=True, exist_ok=True)
    for item in items:
        sliced = subgraph.slice(graph, item.id)
        if sliced is None:
            continue
        view = placer.place(sliced, False)
        payload = {
            "page_title": sliced.page_title,
            "repo": graph.repo,
            "repo_url": "",
            "view": view.model_dump(),
        }
        target = endpoint_dir / f"{endpoint_slug(item.id)}.json"
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return len(items)

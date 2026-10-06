import dataclasses
import json
import re
from pathlib import Path

from endpoint_detail_fixture import EndpointDetailFixtureWriter
from render.placement.flow_page_placer_factory import build_flow_page_placer
from route_fixture import RouteFixtureSlices

from shared.flow_endpoints.endpoint_catalog import EndpointCatalog
from shared.flow_endpoints.endpoint_items import EndpointItem
from shared.flow_endpoints.endpoint_subgraph import EndpointSubgraph
from shared.flow_endpoints.factory import build_route_subgraph
from shared.flow_endpoints.link_resolver import LinkResolver
from shared.flow_endpoints.owner_subgraph import OwnerSubgraph
from shared.flow_endpoints.shared_owner_index import SharedOwnerIndex
from shared.models.flow_graph import FlowGraph


def endpoint_slug(entry_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", entry_id)


def helper_slug(owner_fqn: str) -> str:
    return f"helper_{endpoint_slug(owner_fqn)}"


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


def _links_payload(links: dict) -> dict:
    return {node_id: dataclasses.asdict(link) for node_id, link in links.items()}


def _payload(graph: FlowGraph, sliced: FlowGraph, view, links: dict) -> dict:
    return {
        "page_title": sliced.page_title,
        "repo": graph.repo,
        "repo_url": "",
        "view": view.model_dump(),
        "links": _links_payload(links),
    }


def _write(target: Path, payload: dict) -> None:
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_repo_home_fixture(
    graph: FlowGraph, fixture_dir: Path, repo_path: Path | None = None
) -> int:
    catalog = EndpointCatalog()
    subgraph = EndpointSubgraph()
    owner_subgraph = OwnerSubgraph(subgraph)
    owner_index = SharedOwnerIndex()
    resolver = LinkResolver()
    placer = build_flow_page_placer()
    route_slices = RouteFixtureSlices(build_route_subgraph())
    detail_writer = EndpointDetailFixtureWriter(repo_path)
    items = catalog.items(graph)
    owners = owner_index.owners(graph)
    nodes_by_id = {node.id: node for node in graph.nodes}
    home = {
        "repo": graph.repo,
        "title": graph.repo,
        "description": graph.page_title,
        "endpoints": [_summary(i) for i in items if i.is_route],
        "entry_points": [_summary(i) for i in items if not i.is_route],
    }
    fixture_dir.mkdir(parents=True, exist_ok=True)
    _write(fixture_dir / "repo_home.json", home)
    endpoint_dir = fixture_dir / "endpoints"
    endpoint_dir.mkdir(parents=True, exist_ok=True)
    helper_targets: set[str] = set()
    for item in items:
        node = nodes_by_id.get(item.id)
        if node is not None:
            detail_writer.write(graph, node, item.id, endpoint_dir / f"detail_{endpoint_slug(item.id)}.json")
        if node is not None:
            for handler, route_slice in route_slices.slices(graph, node):
                route_view = placer.place(route_slice, False)
                route_links = resolver.resolve(route_slice, owners, item.id)
                helper_targets.update(x.target for x in route_links.values() if x.kind == "helper")
                route_payload = _payload(graph, route_slice, route_view, route_links)
                route_payload["route"] = route_slice.meta["route"]
                route_payload["happy"] = route_slice.meta["happy"]
                name = f"route_{endpoint_slug(item.id)}__{endpoint_slug(handler)}.json"
                _write(endpoint_dir / name, route_payload)
        sliced = subgraph.slice(graph, item.id)
        if sliced is None:
            continue
        view = placer.place(sliced, False)
        links = resolver.resolve(sliced, owners, item.id)
        helper_targets.update(link.target for link in links.values() if link.kind == "helper")
        payload = _payload(graph, sliced, view, links)
        _write(endpoint_dir / f"{endpoint_slug(item.id)}.json", payload)
    for owner_fqn in sorted(helper_targets):
        sliced = owner_subgraph.slice(graph, owner_fqn)
        if sliced is None:
            continue
        view = placer.place(sliced, False)
        links = resolver.resolve(sliced, owners, owner_fqn)
        payload = _payload(graph, sliced, view, links)
        _write(endpoint_dir / f"{helper_slug(owner_fqn)}.json", payload)
    return len(items)

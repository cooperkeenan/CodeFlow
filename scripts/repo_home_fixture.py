from pathlib import Path

from endpoint_detail_fixture import EndpointDetailFixtureWriter
from group_fixture import GroupFixtureWriter, endpoint_slug, fixture_payload, write_json
from render.placement.flow_page_placer_factory import build_flow_page_placer

from shared.flow_endpoints.endpoint_catalog import EndpointCatalog
from shared.flow_endpoints.endpoint_items import EndpointItem
from shared.flow_endpoints.endpoint_subgraph import EndpointSubgraph
from shared.flow_endpoints.factory import (
    build_group_overview,
    build_group_subgraph,
    build_group_tree,
)
from shared.flow_endpoints.link_resolver import LinkResolver
from shared.flow_endpoints.owner_subgraph import OwnerSubgraph
from shared.flow_endpoints.shared_owner_index import SharedOwnerIndex
from shared.models.flow_graph import FlowGraph


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


def write_repo_home_fixture(
    graph: FlowGraph, fixture_dir: Path, repo_path: Path | None = None
) -> int:
    catalog = EndpointCatalog()
    subgraph = EndpointSubgraph()
    owner_subgraph = OwnerSubgraph(subgraph)
    owner_index = SharedOwnerIndex()
    resolver = LinkResolver()
    placer = build_flow_page_placer()
    detail_writer = EndpointDetailFixtureWriter(repo_path)
    group_writer = GroupFixtureWriter(
        build_group_subgraph(), build_group_overview(), resolver, placer, detail_writer
    )
    forest = build_group_tree().build(graph)
    group_ids = {g.id for g in forest.preorder()}
    items = catalog.items(graph)
    owners = owner_index.owners(graph)
    nodes_by_id = {node.id: node for node in graph.nodes}
    home = {
        "repo": graph.repo,
        "title": graph.repo,
        "description": graph.page_title,
        "endpoints": [_summary(i) for i in items if i.is_route],
        "entry_points": [_summary(i) for i in items if not i.is_route],
        "groups": group_writer.summaries(forest),
    }
    fixture_dir.mkdir(parents=True, exist_ok=True)
    write_json(fixture_dir / "repo_home.json", home)
    endpoint_dir = fixture_dir / "endpoints"
    endpoint_dir.mkdir(parents=True, exist_ok=True)
    helper_targets: set[str] = set()
    for item in items:
        node = nodes_by_id.get(item.id)
        if node is None or item.id in group_ids:
            continue
        detail_writer.write(graph, node, item.id, endpoint_dir / f"detail_{endpoint_slug(item.id)}.json")
        sliced = subgraph.slice(graph, item.id)
        if sliced is None:
            continue
        view = placer.place(sliced, False)
        links = resolver.resolve(sliced, owners, item.id)
        helper_targets.update(link.target for link in links.values() if link.kind == "helper")
        write_json(endpoint_dir / f"{endpoint_slug(item.id)}.json", fixture_payload(graph, sliced, view, links))
    helper_targets.update(group_writer.write_all(graph, forest, owners, endpoint_dir))
    for owner_fqn in sorted(helper_targets):
        sliced = owner_subgraph.slice(graph, owner_fqn)
        if sliced is None:
            continue
        view = placer.place(sliced, False)
        links = resolver.resolve(sliced, owners, owner_fqn)
        payload = fixture_payload(graph, sliced, view, links)
        write_json(endpoint_dir / f"{helper_slug(owner_fqn)}.json", payload)
    return len(items)

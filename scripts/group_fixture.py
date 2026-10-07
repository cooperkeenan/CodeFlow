import dataclasses
import json
import re
from pathlib import Path

from endpoint_detail_fixture import EndpointDetailFixtureWriter
from render.placement.flow_page_placer import FlowPagePlacer

from shared.flow_endpoints.endpoint_group import EndpointGroup, GroupForest
from shared.flow_endpoints.group_overview import GroupOverview
from shared.flow_endpoints.group_subgraph import GroupSubgraph
from shared.flow_endpoints.link_resolver import LinkResolver
from shared.models.flow_graph import FlowGraph


def endpoint_slug(entry_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", entry_id)


def write_json(target: Path, payload: dict) -> None:
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def fixture_payload(graph: FlowGraph, sliced: FlowGraph, view, links: dict) -> dict:
    return {
        "page_title": sliced.page_title,
        "repo": graph.repo,
        "repo_url": "",
        "view": view.model_dump(),
        "links": {node_id: dataclasses.asdict(link) for node_id, link in links.items()},
    }


class GroupFixtureWriter:
    def __init__(
        self,
        subgraph: GroupSubgraph,
        overview: GroupOverview,
        resolver: LinkResolver,
        placer: FlowPagePlacer,
        detail_writer: EndpointDetailFixtureWriter,
    ) -> None:
        self._subgraph = subgraph
        self._overview = overview
        self._resolver = resolver
        self._placer = placer
        self._detail_writer = detail_writer

    def summaries(self, forest: GroupForest) -> list[dict]:
        return [self._summary(forest, g) for g in forest.preorder()]

    def write_all(
        self, graph: FlowGraph, forest: GroupForest, owners: dict, endpoint_dir: Path
    ) -> set[str]:
        helper_targets: set[str] = set()
        nodes_by_id = {node.id: node for node in graph.nodes}
        for group in forest.preorder():
            slug = endpoint_slug(group.id)
            sliced = (
                self._subgraph.slice(graph, forest, group.id)
                if group.is_leaf
                else self._overview.slice(graph, forest, group.id)
            )
            node = nodes_by_id.get(group.entry_id)
            if sliced is None or node is None:
                continue
            view = self._placer.place(sliced, False)
            links = self._resolver.resolve(sliced, owners, group.entry_id)
            helper_targets.update(x.target for x in links.values() if x.kind == "helper")
            payload = fixture_payload(graph, sliced, view, links)
            payload["group"] = sliced.meta["group"]
            payload["paths"] = sliced.meta["paths"]
            write_json(endpoint_dir / f"{slug}.json", payload)
            routes = [(r.handler_fqn, r.method, r.path) for r in group.routes] if group.is_leaf else []
            extra = {
                "id": group.id,
                "title": group.name,
                "group": self._summary(forest, group),
                "children": [self._summary(forest, c) for c in forest.children(group.id)],
            }
            self._detail_writer.write(
                graph, node, group.entry_id, endpoint_dir / f"detail_{slug}.json", routes, extra
            )
        return helper_targets

    def _summary(self, forest: GroupForest, group: EndpointGroup) -> dict:
        depth, parent = 0, group.parent_id
        while parent is not None:
            depth += 1
            parent = getattr(forest.find(parent), "parent_id", None)
        return {
            "id": group.id,
            "parent_id": group.parent_id,
            "name": group.name,
            "route_count": group.route_count,
            "is_leaf": group.is_leaf,
            "depth": depth,
        }

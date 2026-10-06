import dataclasses

from gateway.clients.render_client import RenderClient

from shared.flow_endpoints.link_resolver import LinkResolver
from shared.flow_endpoints.shared_owner_index import SharedOwnerIndex
from shared.models.flow_graph import FlowGraph


class FlowViewRenderer:
    def __init__(
        self,
        render_client: RenderClient,
        owner_index: SharedOwnerIndex,
        link_resolver: LinkResolver,
    ) -> None:
        self._render = render_client
        self._owner_index = owner_index
        self._link_resolver = link_resolver

    async def render(
        self, repo: str, sliced: FlowGraph, graph: FlowGraph, current_root: str
    ) -> dict:
        rendered = await self._render.render(sliced.model_dump(mode="json"), lane_headers=False)
        owners = self._owner_index.owners(graph)
        links = self._link_resolver.resolve(sliced, owners, current_root)
        return {
            "page_title": sliced.page_title,
            "repo": repo,
            "repo_url": "",
            "view": rendered["view"],
            "links": {node_id: dataclasses.asdict(link) for node_id, link in links.items()},
        }

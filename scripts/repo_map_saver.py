from shared.models.diagram_template import RenderedView
from shared.models.flow_graph import FlowGraph
from shared.models.repo_blueprint import RepoBlueprint
from shared.repo_map_store.repo_map_store import RepoMapStore


class RepoMapSaver:
    def __init__(self, store: RepoMapStore) -> None:
        self._store = store

    async def save(
        self,
        user_id: int,
        repo: str,
        graph: FlowGraph,
        view: RenderedView,
        source: str,
    ) -> None:
        profile = RepoBlueprint(architecture_type="unknown", language="python", framework="")
        payload = {
            "repo": repo,
            "profile": profile.model_dump(mode="json"),
            "trace": {"flow_graph": graph.model_dump(mode="json")},
            "diagram": {"view": view.model_dump(mode="json")},
        }
        await self._store.save(user_id, repo, source, payload)

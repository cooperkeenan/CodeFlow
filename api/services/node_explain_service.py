import hashlib
import json

from clients.explain_client import ExplainClient
from services.repo_map_service import RepoMapService
from services.step_tree_labeler import StepTreeLabeler
from services.symbol_context_resolver import SymbolContextResolver
from shared.explain_prompt_version import PROMPT_VERSION
from shared.explanation_store.explanation_store import ExplanationStore

_SEPARATOR = "\x1f"


class NodeExplainService:
    def __init__(
        self,
        repo_map_service: RepoMapService,
        resolver: SymbolContextResolver,
        explain_client: ExplainClient,
        explanation_store: ExplanationStore,
        step_labeler: StepTreeLabeler,
    ) -> None:
        self._repo_maps = repo_map_service
        self._resolver = resolver
        self._explain_client = explain_client
        self._store = explanation_store
        self._step_labeler = step_labeler

    async def explain(self, user_id: int, repo: str, node_id: str) -> dict | None:
        detail = await self._repo_maps.get(user_id, repo)
        if detail is None:
            return None
        flow_graph = detail.map.trace.get("flow_graph", {})
        symbol_context = flow_graph.get("meta", {}).get("symbol_context")
        if symbol_context is None:
            return None
        focus_fqn = symbol_context.get("nodes", {}).get(node_id)
        if focus_fqn is None:
            return None
        functions = symbol_context.get("functions", {})
        classes = symbol_context.get("classes", {})

        resolved = self._resolver.resolve_focus(focus_fqn, functions, classes)
        if resolved is None:
            return None
        primary_kind, primary_fqn, member_fqns = resolved

        helper_fqns = self._resolver.resolve_helpers(primary_kind, primary_fqn, member_fqns, functions)
        symbol_fqns = member_fqns if primary_kind == "class" else [primary_fqn]

        file_cache: dict[str, dict | None] = {}
        symbols = await self._slices(symbol_fqns, functions, classes, repo, file_cache)
        helpers = await self._slices(helper_fqns, functions, classes, repo, file_cache)

        payload = {
            "node_id": node_id,
            "node_label": self._node_label(flow_graph, node_id),
            "service": self._resolver.field(primary_fqn, "service", functions, classes),
            "module": self._resolver.field(primary_fqn, "module", functions, classes),
            "cls": classes.get(primary_fqn, {}).get("name", "") if primary_kind == "class" else "",
            "focus_fqn": primary_fqn,
            "symbols": symbols,
            "helpers": helpers,
        }

        sources = {s["fqn"]: s["source"] for s in (*symbols, *helpers)}
        steps = self._resolver.steps_for([*symbol_fqns, *helper_fqns], functions)
        payload["steps"] = self._step_labeler.flatten(steps)

        fingerprint = self._fingerprint(primary_fqn, symbols, helpers, steps)
        cached = await self._store.get(fingerprint)
        if cached is not None:
            labeled_steps = self._step_labeler.apply(steps, cached.get("step_labels", {}))
            return {"explanation": cached, "sources": sources, "steps": labeled_steps}

        response = await self._explain_client.explain(payload)
        explanation = response["explanation"]
        await self._store.put(fingerprint, repo, node_id, explanation)
        labeled_steps = self._step_labeler.apply(steps, explanation.get("step_labels", {}))
        return {"explanation": explanation, "sources": sources, "steps": labeled_steps}

    async def _slices(
        self, fqns: list[str], functions: dict, classes: dict, repo: str, file_cache: dict
    ) -> list[dict]:
        slices = [await self._resolver.slice_for(f, functions, classes, repo, file_cache) for f in fqns]
        return [s for s in slices if s is not None]

    def _node_label(self, flow_graph: dict, node_id: str) -> str:
        for node in flow_graph.get("nodes", []):
            if node.get("id") == node_id:
                return node.get("label", "")
        return ""

    def _fingerprint(
        self, focus_fqn: str, symbols: list[dict], helpers: list[dict], steps: dict[str, list]
    ) -> str:
        pairs = sorted((s["fqn"], s["source"]) for s in (*symbols, *helpers))
        parts = [PROMPT_VERSION, focus_fqn]
        for fqn, source in pairs:
            parts.append(fqn)
            parts.append(source)
        parts.append(json.dumps(steps, sort_keys=True))
        return hashlib.sha256(_SEPARATOR.join(parts).encode("utf-8")).hexdigest()

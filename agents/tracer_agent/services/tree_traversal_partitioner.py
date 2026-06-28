import json
from collections import deque

from services.evidence_partitioner import EvidenceChunk
from shared.models.repo_blueprint import RepoBlueprint


class TreeTraversalPartitioner:
    def __init__(self, token_budget: int, max_components: int) -> None:
        self._budget = token_budget
        self._max_components = max_components

    def partition(self, evidence: dict, blueprint: RepoBlueprint) -> list[EvidenceChunk]:
        signatures = evidence.get("signatures", {})
        if not signatures:
            return []
        adjacency = self._build_adjacency(evidence, set(signatures))
        seeds = self._find_entry_points(signatures, adjacency)
        return self._bfs_chunks(seeds, adjacency, evidence, signatures)

    def _build_adjacency(self, evidence: dict, known: set[str]) -> dict[str, list[str]]:
        adj: dict[str, list[str]] = {n: [] for n in known}
        for key in ("confirmed_edges", "call_edges"):
            for edge in evidence.get(key, []):
                src = edge.get("from")
                tgt = edge.get("to")
                if src in known and tgt in known and tgt not in adj.get(src, []):
                    adj.setdefault(src, []).append(tgt)
        return adj

    def _find_entry_points(self, signatures: dict, adjacency: dict[str, list[str]]) -> list[str]:
        has_incoming: set[str] = set()
        for targets in adjacency.values():
            has_incoming.update(targets)
        roots = sorted(n for n in signatures if n not in has_incoming)
        return roots if roots else sorted(signatures)[:1]

    def _bfs_chunks(
        self,
        seeds: list[str],
        adjacency: dict[str, list[str]],
        evidence: dict,
        signatures: dict,
    ) -> list[EvidenceChunk]:
        chunks: list[EvidenceChunk] = []
        visited: set[str] = set()
        queue: deque[str] = deque(seeds)
        batch: list[str] = []
        index = 0

        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            if batch and self._too_big(batch + [node], evidence):
                chunks.append(EvidenceChunk(label=f"layer:{index}", evidence=self._subset(batch, evidence)))
                index += 1
                batch = []
            visited.add(node)
            batch.append(node)
            for child in adjacency.get(node, []):
                if child not in visited:
                    queue.append(child)

        if batch:
            chunks.append(EvidenceChunk(label=f"layer:{index}", evidence=self._subset(batch, evidence)))
            index += 1

        unreachable = sorted(n for n in signatures if n not in visited)
        fallback: list[str] = []
        for name in unreachable:
            if fallback and self._too_big(fallback + [name], evidence):
                chunks.append(EvidenceChunk(label=f"layer:{index}", evidence=self._subset(fallback, evidence)))
                index += 1
                fallback = []
            fallback.append(name)
        if fallback:
            chunks.append(EvidenceChunk(label=f"layer:{index}", evidence=self._subset(fallback, evidence)))

        return chunks

    def _subset(self, names: list[str], evidence: dict) -> dict:
        name_set = set(names)
        edge_keys = ("import_edges", "call_edges", "http_edges", "confirmed_edges")
        return {
            "signatures": {n: evidence["signatures"][n] for n in name_set},
            **{k: [e for e in evidence.get(k, []) if e.get("from") in name_set] for k in edge_keys},
        }

    def _too_big(self, names: list[str], evidence: dict) -> bool:
        if len(names) > self._max_components:
            return True
        return self._est_tokens(self._subset(names, evidence)) > self._budget

    def _est_tokens(self, payload: dict) -> int:
        return len(json.dumps(payload)) // 4

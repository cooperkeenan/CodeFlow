import json
from dataclasses import dataclass

from services.component_placer import ComponentPlacer
from shared.models.repo_blueprint import RepoBlueprint


@dataclass
class EvidenceChunk:
    label: str
    evidence: dict
    breadcrumb: str | None = None


class EvidencePartitioner:
    def __init__(self, placer: ComponentPlacer, token_budget: int, max_components: int) -> None:
        self._placer = placer
        self._budget = token_budget
        self._max_components = max_components

    def partition(self, evidence: dict, blueprint: RepoBlueprint) -> list[EvidenceChunk]:
        index = self._placer.dir_index(blueprint)
        module_buckets: dict[str, list[str]] = {}
        name_to_zone: dict[str, str] = {}

        for name in sorted(evidence["signatures"]):
            sig = evidence["signatures"][name]
            placement = self._placer.place(sig["file_path"], index)
            root, zone = placement if placement is not None else ("unplaced", "unplaced")
            module_buckets.setdefault(root, []).append(name)
            name_to_zone[name] = zone

        packable: list[tuple[str, list[str]]] = []
        oversized: list[EvidenceChunk] = []
        for root in sorted(module_buckets):
            names = module_buckets[root]
            if self._too_big(names, evidence):
                oversized.extend(self._split_by_zone(root, names, name_to_zone, evidence))
            else:
                packable.append((root, names))
        return self._pack(packable, evidence) + oversized

    def _pack(self, modules: list[tuple[str, list[str]]], evidence: dict) -> list[EvidenceChunk]:
        chunks: list[EvidenceChunk] = []
        roots: list[str] = []
        names: list[str] = []
        for root, mod_names in modules:
            if names and self._too_big(names + mod_names, evidence):
                chunks.append(self._chunk(roots, names, evidence))
                roots, names = [], []
            roots.append(root)
            names = names + mod_names
        if names:
            chunks.append(self._chunk(roots, names, evidence))
        return chunks

    def _split_by_zone(
        self,
        root: str,
        names: list[str],
        name_to_zone: dict[str, str],
        evidence: dict,
    ) -> list[EvidenceChunk]:
        zone_buckets: dict[str, list[str]] = {}
        for name in sorted(names):
            zone_buckets.setdefault(name_to_zone[name], []).append(name)

        chunks: list[EvidenceChunk] = []
        for zone in sorted(zone_buckets):
            zone_names = zone_buckets[zone]
            if self._too_big(zone_names, evidence):
                chunks.extend(self._split_by_group(root, zone, zone_names, evidence))
            else:
                chunks.append(EvidenceChunk(
                    label=f"zone:{root}:{zone}", evidence=self._subset(zone_names, evidence)
                ))
        return chunks

    def _split_by_group(
        self,
        root: str,
        zone: str,
        names: list[str],
        evidence: dict,
    ) -> list[EvidenceChunk]:
        chunks: list[EvidenceChunk] = []
        group: list[str] = []
        group_index = 0

        for name in sorted(names):
            if group and self._too_big(group + [name], evidence):
                chunks.append(EvidenceChunk(
                    label=f"zone:{root}:{zone}#{group_index}", evidence=self._subset(group, evidence)
                ))
                group_index += 1
                group = []
            group.append(name)

        if group:
            chunks.append(EvidenceChunk(
                label=f"zone:{root}:{zone}#{group_index}", evidence=self._subset(group, evidence)
            ))
        return chunks

    def _chunk(self, roots: list[str], names: list[str], evidence: dict) -> EvidenceChunk:
        label = "modules:" + "+".join(r.rstrip("/").rsplit("/", 1)[-1] or r for r in roots)
        return EvidenceChunk(label=label, evidence=self._subset(names, evidence))

    def _too_big(self, names: list[str], evidence: dict) -> bool:
        if len(names) > self._max_components:
            return True
        return self._est_tokens(self._subset(names, evidence)) > self._budget

    def _subset(self, names: list[str] | set[str], evidence: dict) -> dict:
        name_set = set(names)
        edge_keys = ("import_edges", "call_edges", "http_edges", "confirmed_edges")
        return {
            "signatures": {n: evidence["signatures"][n] for n in name_set},
            **{
                k: [e for e in evidence.get(k, []) if e.get("from") in name_set]
                for k in edge_keys
            },
        }

    def _est_tokens(self, payload: dict) -> int:
        return len(json.dumps(payload)) // 4

from collections.abc import Sequence

from models.call_site import CallSite
from models.effect_site import EffectSite
from models.project_index import ProjectIndex
from services.analysis.effect_registry import RULES
from shared.models.flow_graph import EffectKind

_STORE_KIND: EffectKind = "database"
_DOMINANCE = 0.8


class StoreEffectSurfacer:
    def surface(
        self, effects: Sequence[EffectSite], index: ProjectIndex, sites: Sequence[CallSite]
    ) -> tuple[EffectSite, ...]:
        boundaries = self._boundaries(index, sites)
        consumed: set[str] = set()
        folded: list[EffectSite] = []
        for class_fqn, kind in boundaries.items():
            inner = [e for e in effects if self._owned_by(e, class_fqn) and e.kind == kind]
            if not inner:
                continue
            consumed.update(e.id for e in inner)
            folded.append(self._boundary_effect(class_fqn, kind, inner, index))
        kept = [e for e in effects if e.id not in consumed]
        return tuple(kept + folded)

    def _boundaries(self, index: ProjectIndex, sites: Sequence[CallSite]) -> dict[str, EffectKind]:
        result: dict[str, EffectKind] = {}
        for class_fqn in index.classes:
            if self._is_store(class_fqn):
                result[class_fqn] = _STORE_KIND
        for class_fqn, kind in self._dominant(index, sites).items():
            result.setdefault(class_fqn, kind)
        return result

    def _dominant(self, index: ProjectIndex, sites: Sequence[CallSite]) -> dict[str, EffectKind]:
        counts: dict[str, dict[str, int]] = {}
        for site in sites:
            class_fqn = self._class_of(site.caller, index)
            if class_fqn is None:
                continue
            for target in site.targets:
                if target.fqn.startswith("ext:"):
                    root = target.fqn[4:].split(".")[0]
                    counts.setdefault(class_fqn, {})
                    counts[class_fqn][root] = counts[class_fqn].get(root, 0) + 1
        return self._dominant_kinds(counts)

    def _dominant_kinds(self, counts: dict[str, dict[str, int]]) -> dict[str, EffectKind]:
        result: dict[str, EffectKind] = {}
        for class_fqn, roots in counts.items():
            total = sum(roots.values())
            root, top = max(roots.items(), key=lambda item: item[1])
            if total and top / total >= _DOMINANCE:
                kind = self._kind_of_root(root)
                if kind is not None:
                    result[class_fqn] = kind
        return result

    def _kind_of_root(self, root: str) -> EffectKind | None:
        for rule in RULES:
            if root in rule.roots:
                return rule.kind
        return None

    def _boundary_effect(
        self, class_fqn: str, kind: EffectKind, inner: list[EffectSite], index: ProjectIndex
    ) -> EffectSite:
        line = index.classes[class_fqn].span.line if class_fqn in index.classes else 0
        target = next((e.target for e in inner if e.target), "")
        return EffectSite(
            id=f"eff:{class_fqn}:{line}",
            owner=class_fqn,
            kind=kind,
            target=target,
            method="",
            line=line,
            context=(),
        )

    def _owned_by(self, effect: EffectSite, class_fqn: str) -> bool:
        return effect.owner == class_fqn or effect.owner.startswith(f"{class_fqn}.")

    def _class_of(self, caller: str, index: ProjectIndex) -> str | None:
        record = index.functions.get(caller)
        return record.cls if record is not None else None

    def _is_store(self, class_fqn: str) -> bool:
        return class_fqn.endswith("Store") or "_store." in class_fqn or "Store." in class_fqn

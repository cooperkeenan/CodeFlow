import logging

from models.repo_skeleton import ModuleSkeleton, RepoSkeleton

from shared.models.repo_blueprint import ModulePlan, RepoBlueprint, ZonePlan

logger = logging.getLogger(__name__)


class BlueprintValidator:
    def validate(self, raw: dict, skeleton: RepoSkeleton) -> RepoBlueprint:
        raw_list = [m for m in raw.get("modules", []) if isinstance(m, dict)]
        by_name = {m.get("name"): m for m in raw_list}
        by_root = {m.get("root_path"): m for m in raw_list}
        modules = [
            self._module(sk, by_name.get(sk.name) or by_root.get(sk.root_path) or {})
            for sk in skeleton.modules
        ]
        return RepoBlueprint(
            architecture_type=raw.get("architecture_type") or "unknown",
            language=raw.get("language") or "unknown",
            framework=raw.get("framework") or "unknown",
            patterns=[str(p) for p in raw.get("patterns", []) if isinstance(p, str)],
            modules=modules,
        )

    def _module(self, sk: ModuleSkeleton, raw_module: dict) -> ModulePlan:
        valid_dirs = {d.path for d in sk.directories}
        zones, assigned = self._zones(raw_module.get("zones", []), valid_dirs)
        leftover = sorted(valid_dirs - assigned)
        if leftover:
            logger.info("Module %s: %d dir(s) fell back to 'other'", sk.name, len(leftover))
            zones.append(ZonePlan(name="other", description="Unlabelled directories", directories=leftover))
        if not zones:
            zones = [ZonePlan(name="module", directories=sorted(valid_dirs))]
        return ModulePlan(
            name=sk.name,
            description=raw_module.get("description") or "",
            root_path=sk.root_path,
            style=raw_module.get("style") or "",
            zones=zones,
        )

    def _zones(self, raw_zones: list, valid_dirs: set[str]) -> tuple[list[ZonePlan], set[str]]:
        by_name: dict[str, ZonePlan] = {}
        order: list[str] = []
        assigned: set[str] = set()
        for rz in raw_zones:
            if not isinstance(rz, dict):
                continue
            dirs = [
                d for d in rz.get("directories", [])
                if d in valid_dirs and d not in assigned
            ]
            assigned.update(dirs)
            if not dirs:
                continue
            name = str(rz.get("name") or "zone").strip().lower()
            if name not in by_name:
                by_name[name] = ZonePlan(name=name, description=str(rz.get("description") or ""), directories=list(dirs))
                order.append(name)
            else:
                by_name[name].directories.extend(dirs)
        return [by_name[n] for n in order], assigned

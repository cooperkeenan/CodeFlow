# PBI 1 — Extract `ComponentPlacer`

## Goal
Lift the directory-prefix placement logic out of `SpecAssembler` into a reusable
`agents/tracer_agent/services/component_placer.py`, and have `SpecAssembler` depend on it via
constructor injection. **No behavior change** — this is a pure refactor that the chunking work
(PBI 2/3) will reuse to map signatures → module/zone.

## Read first
- `agents/tracer_agent/services/spec_assembler.py` — source of the logic.
- `agents/tracer_agent/dependencies.py` — how `SpecAssembler` is constructed (`get_spec_assembler`).
- `CLAUDE.md` — standards (≤150 lines/file, constructor injection, type annotations, no comments/
  docstrings/logging/tests, no unused imports, one class per file).

## What to build

### New file `agents/tracer_agent/services/component_placer.py`
A `ComponentPlacer` class encapsulating the current `_dir_index` + `_place` logic:
```python
from shared.models.repo_blueprint import RepoBlueprint

class ComponentPlacer:
    def dir_index(self, blueprint: RepoBlueprint) -> list[tuple[str, str, str]]: ...
    def place(self, file_path: str, index: list[tuple[str, str, str]]) -> tuple[str, str] | None: ...
```
- `dir_index` returns `(directory, module.root_path, zone.name)` tuples sorted by directory length
  descending — identical to `SpecAssembler._dir_index` (`spec_assembler.py:43-51`).
- `place` returns `(root, zone)` for the longest directory prefix matching `file_path`, else `None` —
  identical to `SpecAssembler._place` (`spec_assembler.py:53-57`).

### Refactor `agents/tracer_agent/services/spec_assembler.py`
- Add `def __init__(self, placer: ComponentPlacer) -> None: self._placer = placer`.
- In `assemble`, replace `self._dir_index(blueprint)` with `self._placer.dir_index(blueprint)` and
  `self._place(component.file_path, index)` with `self._placer.place(component.file_path, index)`.
- Delete the now-moved `_dir_index` and `_place` methods. Everything else (`_components`, `_edges`,
  `_actors`, module skeleton building) stays exactly the same.

### Wire DI in `agents/tracer_agent/dependencies.py`
- Add `get_component_placer() -> ComponentPlacer: return ComponentPlacer()`.
- Change `get_spec_assembler` to inject it:
  `def get_spec_assembler(placer: ComponentPlacer = Depends(get_component_placer)) -> SpecAssembler: return SpecAssembler(placer)`.

## Acceptance / verification
- All three files parse; each ≤150 lines; no unused imports.
- **Behavior identical.** Throwaway check (don't commit): load `shared/outputs/tracer_output.json`,
  pull out the `diagram_spec`'s components with their `file_path`s and the blueprint, build a fake
  `raw` dict from those components, and confirm `SpecAssembler(ComponentPlacer()).assemble(blueprint,
  raw, arch)` places every component into the same module/zone as in the stored spec. (Run with repo
  root + `agents/tracer_agent` on `sys.path`, cwd at `agents/tracer_agent`.)

## Out of scope
Do not touch any other file. No chunking logic yet.

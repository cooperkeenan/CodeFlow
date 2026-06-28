# PBI A — Neighborhood contraction helper (pure)

## Goal
Add a new pure module `agents/layout_agent/services/_neighborhood.py` that encapsulates the
"service-centric" graph reasoning the view builder needs. **No existing behavior changes in this
PBI** — only the new module is added. It will be wired up in PBI B and PBI C.

## Why
The high-level component view currently shows thin tool wrappers (e.g. `BuildCallGraphTool`) instead
of the services they delegate to (`CallGraphService`). The wrappers sit one hop above the services in
the call graph. We need reusable, testable logic to (a) pull each thin wrapper's service one hop
deeper and fold the wrapper into it, and (b) for drill-down, fold a wrapper into the service it
wraps and pull the upstream caller up.

## Context — existing code to reuse (do NOT reinvent)
`agents/layout_agent/services/_graph_contraction.py` already defines:
```python
_PRIMARY = frozenset({"service", "orchestrator", "repository", "entry"})
_ADAPTER = frozenset({"tool", "client", "helper"})

@dataclass
class ContractionResult:
    names: set[str]
    edges: list[tuple[str, str]]
    folded: dict[str, list[str]]   # survivor -> [folded adapters]

def contract(names: set[str], edges: list[tuple[str, str]], roles: dict[str, str]) -> ContractionResult: ...
```
`contract()` folds any adapter (role in `_ADAPTER`) that has exactly one callee **within the given
`names` set** into that callee.

`shared/models/diagram_spec.py` defines:
```python
class Component(BaseModel):
    name: str
    description: str
    file_path: str
    io: ComponentIO | None = None
    children: list[str] = []
    role: str = ""
    tier: ComponentTier = "primary"
    nested: bool = False

class Edge(BaseModel):
    source: str
    target: str
    edge_type: EdgeType   # "http" | "import" | "database" | "event" | "call" | "sequence"
    primary: bool = True
```

## What to build — `agents/layout_agent/services/_neighborhood.py`

Constraints: ≤150 lines, full type annotations on every signature, dataclasses for the value objects,
**no logging, no inline/docstring comments, no tests**. Import `_PRIMARY`, `_ADAPTER`, `contract`,
`ContractionResult` from `services._graph_contraction`. Import `Component`, `Edge` from
`shared.models.diagram_spec` for type hints only.

Implement three pure functions plus two small dataclasses.

### Shared internal helper
Build a "full callee map" once per call from the edge list, skipping `import` edges and self-loops:
```python
def _callee_map(edges: list[Edge]) -> dict[str, list[str]]:
    # name -> ordered unique list of non-import, non-self callees
```

### 1. `single_callee_adapters`
```python
def single_callee_adapters(
    names: set[str], all_comps: dict[str, Component], edges: list[Edge],
) -> dict[str, str]:
```
For each `name in names` whose component role is in `_ADAPTER` and which has **exactly one** callee
in the full callee map, AND that one callee's role is in `_PRIMARY` (so we surface services, not
models/value objects), return `{adapter_name: service_name}`. Skip adapters whose single callee is
not a known component or whose callee role is not primary.

### 2. `contract_steps` — high-level view (PBI B will call this)
```python
@dataclass
class ContractedSteps:
    callees: list[str]
    children: list[str]
    folded: dict[str, list[str]]

def contract_steps(
    focus: str, callees: list[str], children: list[str],
    all_comps: dict[str, Component], edges: list[Edge],
) -> ContractedSteps:
```
Algorithm:
1. `step_set = set(callees) | set(children)`.
2. `adapters = single_callee_adapters(step_set, all_comps, edges)` — wrappers among the steps and the
   services they point at.
3. `expanded = step_set | set(adapters.values())` — pull each wrapper's service one hop deeper in.
4. Build `intra = [(s, t) for (s, t) in full edges if s in expanded and t in expanded and s != t]`
   (exclude import/self). Reuse the callee map or iterate edges directly.
5. `roles = {n: all_comps[n].role if n in all_comps else "" for n in expanded}`.
6. `cr = contract(expanded, intra, roles)` — wrappers fold into their services.
7. Invert `cr.folded` to a `fold_map: {adapter: survivor}`.
8. Remap: `new_callees`/`new_children` = for each original name, take `fold_map.get(name, name)`,
   keep only if it is in `cr.names`, dedup preserving first-seen order.
9. Return `ContractedSteps(new_callees, new_children, cr.folded)`.

### 3. `wrapping_adapters` — drill-down (PBI C will call this)
```python
@dataclass
class WrappedFocus:
    folded: list[str]          # adapter wrappers that wrap `focus`
    pulled_callers: list[str]  # callers one hop above those wrappers

def wrapping_adapters(
    focus: str, callers: list[str], all_comps: dict[str, Component], edges: list[Edge],
) -> WrappedFocus:
```
Algorithm:
1. From `callers`, select those whose component role is in `_ADAPTER` and whose **only** callee (full
   callee map) is `focus`. These are the `folded` wrappers.
2. `pulled_callers` = ordered-unique callers of those wrappers (edges with `target == wrapper`,
   non-import, non-self), excluding `focus` itself and excluding the wrappers.
3. Return `WrappedFocus(folded=sorted-stable list, pulled_callers=...)`. If no wrappers qualify,
   return empty lists.

## Acceptance
- New file only; nothing else modified.
- `python -c "import ast; ast.parse(open('agents/layout_agent/services/_neighborhood.py').read())"`
  parses; file ≤150 lines.
- Functions are pure (no I/O, no globals, no mutation of inputs).
- Manual check against cached data (you may write a throwaway snippet, do not commit it): with the
  `tracer_agent` components, `single_callee_adapters` maps `BuildCallGraphTool→CallGraphService`,
  `BuildEvidenceTool→EvidenceService`, `FetchLayerFilesTool→FileFetchService`; `contract_steps` for
  `TracerService`'s steps yields callees containing those three services (and `GraphValidator`,
  `SpecAssembler`, `CorrectionPromptBuilder`) with the wrappers gone; `wrapping_adapters` for
  `CallGraphService` (caller `BuildCallGraphTool`) returns `folded=["BuildCallGraphTool"]`,
  `pulled_callers=["TracerService"]`.

## Out of scope
Do not modify `_view_builder.py`, `_edge_builder.py`, `_graph_contraction.py`, or anything else.

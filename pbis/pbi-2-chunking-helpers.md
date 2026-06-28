# PBI 2 — Pure chunking helpers

## Goal
Add three pure, deterministic helpers used by the chunked tracer (PBI 4). No wiring into
`TracerService` yet.

## Background — evidence bundle shape (confirmed)
`EvidenceService.build` returns:
```python
{
  "signatures": { "<ComponentName>": {"file_path": str, "public_methods": [...], "imports": [...]} },
  "import_edges":   [{"from": str, "to": str}, ...],
  "call_edges":     [{"from": str, "to": str}, ...],
  "confirmed_edges":[{"from": str, "to": str}, ...],
  "http_edges":     [{"from": str, "to": str}, ...],   # "to" is a URL path or constant, not a class
}
```
Each signature carries its `file_path`, so signatures map to module/zone via `ComponentPlacer`
(PBI 1: `agents/tracer_agent/services/component_placer.py` — `dir_index(blueprint)` /
`place(file_path, index) -> (root, zone) | None`).

## Read first
- `agents/tracer_agent/services/component_placer.py`, `services/evidence_service.py`,
  `shared/models/repo_blueprint.py` (`RepoBlueprint.modules[].zones[].directories`).
- `CLAUDE.md` — standards (≤150 lines/file, dataclasses, type annotations, no comments/docstrings/
  logging/tests, no unused imports, one class per file unless a private detail).

## 1. `agents/tracer_agent/services/evidence_partitioner.py`
```python
@dataclass
class EvidenceChunk:
    label: str
    evidence: dict   # same shape as the full bundle, restricted to this chunk

class EvidencePartitioner:
    def __init__(self, placer: ComponentPlacer, token_budget: int) -> None: ...
    def partition(self, evidence: dict, blueprint: RepoBlueprint) -> list[EvidenceChunk]: ...
```
Algorithm:
- `index = self._placer.dir_index(blueprint)`. For each `name, sig` in `evidence["signatures"]`,
  compute `place(sig["file_path"], index)` → `(root, zone)`; bucket names by `root` (module), and
  remember each name's `zone`. Names that don't place go in a synthetic `"unplaced"` module bucket
  (still emitted as a chunk so nothing is dropped).
- For each module bucket, build a candidate chunk via `_subset(names)` and estimate size with
  `_est_tokens`. If `<= token_budget`, emit one chunk `label=f"module:{root}"`. Otherwise split the
  module's names by `zone` and emit a chunk per zone (`label=f"zone:{root}:{zone}"`). If a single zone
  still exceeds budget, split its names into fixed-size groups (accumulate names until the running
  `_est_tokens` would exceed budget, then start a new group; `label=f"zone:{root}:{zone}#k"`). A single
  indivisible oversized signature gets its own chunk (allowed to exceed budget — log nothing, just
  emit it).
- `_subset(names: set[str]) -> dict`: `signatures` = those names; each of `import_edges/call_edges/
  http_edges/confirmed_edges` filtered to entries whose `"from"` is in `names`. (The chunk sees what
  its own components call, including cross-module targets it should emit http edges for.)
- `_est_tokens(payload: dict) -> int`: `len(json.dumps(payload)) // 4`.
- Determinism: iterate names in `sorted(...)` order so chunk contents are stable.

## 2. `agents/tracer_agent/services/chunk_context_builder.py`
```python
class ChunkContextBuilder:
    def build(self, blueprint: RepoBlueprint, evidence: dict) -> str: ...
```
Return one compact string shared by every chunk so a chunk can resolve **cross-module http** targets:
- A "MODULES" section: one line per module — `name (root_path): zones [..]`.
- An "HTTP CALLS" section: the `evidence["http_edges"]` as `from -> to` lines (deduped), so the LLM can
  match a path like `/layout` to the owning module/entry component per the existing prompt rule.
Keep it small (names/paths only, no signatures).

## 3. `agents/tracer_agent/services/raw_merger.py`
```python
class RawMerger:
    def merge(self, raws: list[dict]) -> dict: ...
```
Concatenate per-chunk LLM `raw` dicts into one with the same shape the assembler expects
(`components`, `edges`, `external_actors`, `entry_points`):
- `components`: dedup by `name` (first occurrence wins), skip non-dict / missing `name`.
- `edges`: dedup by `(source, target, edge_type)`.
- `external_actors`: dedup by `name`.
- `entry_points`: unique, order-preserving.
Be defensive about missing keys (treat as empty list).

## Acceptance / verification (throwaway, do NOT commit a test)
Build a real evidence bundle (in-process: reuse the gather path, or reconstruct from
`shared/outputs/tracer_output.json` signatures if present) and a `RepoBlueprint`, then assert:
1. `partition` covers every signature exactly once across chunks (union of chunk signature keys ==
   full signature keys, disjoint).
2. Each chunk's `_est_tokens` ≤ budget, except a chunk that is a single indivisible signature.
3. With a tiny budget the module chunk splits into zone (and group) chunks; with a huge budget you get
   one chunk per module.
4. `RawMerger.merge` of per-chunk identity raws (build a raw per chunk from its signatures as
   components) reproduces the full component set with no dups.

Run with repo root + `agents/tracer_agent` on `sys.path`, cwd at `agents/tracer_agent`. Delete temp
files after.

## Out of scope
No changes to `tracer_service.py`, `dependencies.py`, or config. Helpers only.

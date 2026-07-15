# F03 — Call resolver

Depends on: F02
Deliverable: `agents/tracer_agent/services/analysis/call_resolver.py` (+ helper files)
Replaces: `CallGraphService` + jarviscg (retired entirely), `AstService._extract_calls`.

## Why

The function-level call graph **with per-call-site control context** is the fact base
for everything. jarviscg cannot supply call-site context and its output was being
collapsed to class names anyway; a project resolver that exploits this codebase
discipline (annotations + constructor injection) is both simpler and stronger.

## Spec

For every `FunctionRecord`, walk its body tracking a context stack; emit `CallSite`s.

```python
@dataclass(frozen=True)
class ControlFrame:
    kind: Literal["if", "match", "try", "loop", "with"]
    site_id: str          # matches F04 DispatchSite.id when kind in {"if","match","try"}
    arm_index: int        # which branch/case/handler the call sits under

@dataclass(frozen=True)
class ResolvedTarget:
    fqn: str
    confidence: Literal["resolved", "inferred"]

@dataclass(frozen=True)
class CallSite:
    caller: str
    line: int
    targets: tuple[ResolvedTarget, ...]   # >1 == polymorphic candidates; empty == dynamic
    context: tuple[ControlFrame, ...]
    in_loop: bool
    call_source: str                       # verbatim call expression, truncated 120 chars
```

**Resolution ladder** — first hit wins; tier noted:

1. Local binding: name assigned earlier in the function from a resolvable expression
   (constructor call, import alias) → `resolved`.
2. Module binding via `ProjectIndex.resolve` → `resolved`.
3. `self.m()` / `cls.m()` → own class, then MRO through resolved bases → `resolved`.
4. `self._dep.m()` → `attr_types[_dep]` annotation:
   a. concrete class → its method, `resolved`;
   b. base with exactly **one** project implementation → that implementation's
      method, `resolved` (indirection, not a decision);
   c. base with **≥2** implementations → all implementations' methods as targets
      (this call site becomes a `polymorphic` dispatch site in F04), `resolved`.
5. **Construction-site binding**: if 4's annotation is abstract but every project
   construction of the owning class passes the same concrete type for that param,
   bind to it → `resolved`. (Composition roots like `dependencies.py` make DI exact.)
6. **Unique-name inference**: method/function name unique across the project index →
   that symbol, `inferred`.
7. Otherwise: `targets = ()` → dynamic. Count it; F04 turns called-`getattr` patterns
   into explicit dynamic dispatch sites.

**Callbacks / higher-order**: a project function passed as an argument
(`retry(self._fetch)`, `map(handler, xs)`) emits an `inferred` CallSite from the
receiving callee (if resolvable) or from the caller otherwise.

**Decorators**: the decorated function keeps its own identity (transparent). Project-
internal decorators additionally emit an `inferred` edge caller→decorator.

Chained attribute bases (`self._a.b.c()`) resolve stepwise through annotations/return
annotations; any unresolved step drops to tier 6/7.

## Non-goals

No flow-sensitive typing beyond straight-line local assignment; no generics/overload
resolution; no cross-process resolution (that is F08's stitching).

## Acceptance

On CodeFlow: `TracerService.trace` yields resolved CallSites into
`FileFetchService.fetch_files`, `TreeTraversalPartitioner.partition`, etc., each with
correct `context` (`ChunkTracer.trace_chunk`'s retry-loop calls flagged `in_loop`);
`ServiceStepPlanner._call`'s `self._llm.messages.create` resolves to `ext:anthropic`;
zero uppercase-heuristic name collisions. Report per-tier resolution counts; on
CodeFlow ≥90% of project-internal call sites must land in tiers 1–5.

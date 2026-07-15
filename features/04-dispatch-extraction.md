# F04 — Dispatch-site extraction

Depends on: F02, F03
Deliverable: `agents/tracer_agent/services/analysis/dispatch_extractor.py`
(+ one visitor/detector file per kind, following the `HttpCallVisitor` style)

## Why

The diagram's decision nodes. A dispatch site is any point where one caller may invoke
one of N alternatives; if-statements are just one of seven realizations. No CFG is
needed — arms, terminality, and reconvergence all read directly off the AST.

## Spec

```python
@dataclass(frozen=True)
class Arm:
    index: int
    label_source: str      # "kind == 'cat'" | "case Foo(...)" | "'cpt'" (dict key) | "POST /trace" | "NeonUserStore" | "ValueError"
    callsites: tuple[CallSite, ...]      # direct calls lexically inside the arm
    terminal: Literal["returns", "raises", "continues", "falls_through"]

@dataclass(frozen=True)
class DispatchSite:
    id: str                # "<owner_fqn>:<line>"
    owner: str
    kind: Literal["branch", "match", "table", "route", "polymorphic", "except", "dynamic"]
    selector_source: str   # condition / subject / key expr / base type, verbatim (≤120 chars)
    selector_reads: tuple[str, ...]   # names + attr chains read by the selector
    arms: tuple[Arm, ...]
    reconverges: bool      # statements exist after the construct in its enclosing block
    span: SourceRef
```

**Detectors** (one file each):

- `branch`: an `if/elif/.../else` chain is ONE site; each `elif` an arm; missing
  `else` adds an implicit fall-through arm with no callsites. Ternaries with calls in
  either branch count. `x and f()` / `x or f()`: out of scope v1 (noise, revisit).
- `match`: subject = selector; one arm per `case` (guards included in `label_source`).
- `except`: `try` body is arm 0; each handler an arm labeled by its exception type;
  `finally` is not an arm. Only sites where ≥1 handler contains project callsites
  survive extraction (a bare `raise`/log handler is recorded with empty callsites and
  will die in F06).
- `table`: module- or class-level dict whose values are all project callables/classes,
  joined to lookup-call sites (`d[k](...)`, `d.get(k, default)(...)`). Also the
  registration idiom: a decorator that inserts into such a dict. Arms = entries,
  `label_source` = literal key repr. Non-literal keys ⇒ treat whole table as one
  dynamic arm set with known targets.
- `route`: framework entry tables. FastAPI first: `FastAPI()`/`APIRouter()` objects,
  `@router.<get|post|put|delete|patch>(path)`, `app.include_router(r, prefix=...)`
  composed to full method+path per arm; handler = the decorated function. The site's
  owner is the app/router's `<module>` function. Design the detector behind a small
  interface so Flask/Django detectors can be added (Open/Closed).
- `polymorphic`: from F03 tier 4c — call sites with ≥2 targets. Arms = one per
  implementation, `label_source` = implementation class name.
- `dynamic`: `getattr(obj, <non-constant>)(...)` and `globals()[k](...)` patterns.
  Arms unknown; keep candidate hints if the name is an f-string with a literal prefix
  (reuse the `_fstring_path` trick to record `handle_*`).

**Terminality**: an arm is `raises`/`returns`/`continues` iff its last executable
statement is that construct (recursively through nested trivial blocks).
**Reconvergence**: true iff the construct is followed by ≥1 statement in its
enclosing block.
**selector_reads**: every `Name` and dotted chain rooted at a name in the selector
expression — F06 uses this for provenance.

## Non-goals

No importance judgment (F06). No effect classification (F05). No boolean-operator
micro-branches. No `while` conditions (loops are badges, not decisions).

## Acceptance

On CodeFlow: `ServiceStepPlanner.plan` yields an `except` site (try arm calls
`_call`/`validate`, handler arm calls `_fallback`); each agent's `routers/` yields a
`route` site with correct method+path arms (e.g. `POST /trace` → `trace`);
`ServiceStepValidator.validate`'s `raw_type in _ALLOWED_TYPES` conditional yields a
`branch` site whose arms have no project callsites (fodder for F06 to reject);
`UserStore` calls yield NO polymorphic site (single impl).

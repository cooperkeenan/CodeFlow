# F05 — Effect detection

Depends on: F02, F03
Deliverable: `agents/tracer_agent/services/analysis/effect_detector.py` + registry
Generalizes: `HttpCallVisitor` (which it replaces).

## Why

Effects are the right-hand edge of the page — the observable outcomes a human thinks
in ("…and then it writes the spec to Neon and returns the diagram"). They are also the
anchor points F08 stitches services together with.

## Spec

```python
@dataclass(frozen=True)
class EffectSite:
    id: str                       # "eff:<owner_fqn>:<line>"
    owner: str
    kind: EffectKind              # from F01
    target: str                   # best-effort hint, "" if unknown
    method: str                   # "POST" etc. for http_out, else ""
    line: int
    context: tuple[ControlFrame, ...]   # same context stack as CallSites
```

Detection is registry-driven: a declarative table mapping external roots (from F02's
`ext:` sentinels) and call shapes to effect kinds. Initial registry:

| ext root | shape | kind | target |
|---|---|---|---|
| httpx, requests, aiohttp | `.get/.post/.put/.delete/.patch/.request(url, …)` | http_out | url arg: literal, f-string via `_fstring_path` logic, or var name |
| anthropic, openai | `.messages.create`, `.chat.completions.create` | llm | `model=` kwarg if literal/constant fqn |
| psycopg, asyncpg, sqlalchemy, databases | execute/fetch/connect | database | table name if first arg literal SQL (regex `FROM\|INTO\|UPDATE\s+(\w+)`) |
| boto3, aioboto3 | client/resource ops | queue or file by service name | bucket/queue arg |
| smtplib, sendgrid, resend | send | email | — |
| builtins / pathlib | `open(_, "w"/"a")`, `Path.write_*` | file | path hint |

Plus two structural detectors:
- **response**: the return of a route handler (owner is a `route` arm target from F04)
  is an implicit `response` effect; `target` = the route's `response_model` annotation
  fqn when present.
- **project stores**: a resolved call into a project class whose fqn matches
  `*_store.*` / `*Store.*` (this repo's persistence convention) that itself contains a
  `database` effect is tagged database at the *store* boundary, so the page shows
  "→ RepoMapStore (db)" not raw psycopg noise. General rule: an effect inside a
  component is surfaced at the outermost project component whose sole purpose is that
  effect (heuristic: class with ≥80% of its callsites hitting one ext root).

Registry lives in one data module; adding a library is a one-line change (Open/Closed).

## Non-goals

No stitching (F08). No attempt to trace env/config-driven URLs beyond the f-string
literal-prefix trick.

## Acceptance

On CodeFlow: the api gateway's httpx calls to the four agents produce `http_out`
effects with path targets (`/trace`, `/profile`, …); every `messages.create` in the
three LLM agents produces an `llm` effect with its model constant; Neon store classes
surface as `database` effects at the store class boundary; `POST /trace`'s handler
yields a `response` effect targeting `TracerResponse`.

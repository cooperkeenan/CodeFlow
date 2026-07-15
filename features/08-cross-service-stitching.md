# F08 — Cross-service stitching

Depends on: F05, F07
Deliverable: `agents/tracer_agent/services/analysis/flow_stitcher.py`

## Why

The single biggest intuition win. Without it, each service's flows are islands and
"one page" is just N small diagrams. With it, the api gateway's `httpx.post("/trace")`
connects into the tracer lane's `POST /trace` entry, and the page shows one continuous
journey per user action — which is exactly how a human narrates a distributed
codebase.

## Spec

Input: the FlowGraph from F07. Output: same graph + `stitch` edges.

### Matching

For every `http_out` effect node with a non-empty path target:

1. Normalize the outbound path: strip scheme/host (env-var and f-string hosts reduce
   to their path suffix via the literal-prefix trick already specified in F05); the
   result is a path string possibly containing `{placeholder}` segments.
2. Normalize each `route` entry arm: method + path template with `{param}` segments.
3. Match on method + segment-wise path comparison where a placeholder matches any
   single segment. Confidence:
   - `resolved`: exact literal match;
   - `inferred`: template match (placeholders involved), or unique-suffix match
     (outbound path's known suffix matches exactly one route in the project).
4. On match: add `FlowEdge(source=effect_id, target=entry_id, kind="stitch",
   confidence=...)`. Multiple matches ⇒ no edge (ambiguous; leave the effect as a
   leaf rather than guess — honesty rule).
5. No match: effect stays a leaf ("calls external API").

### Queue/event stitching (same mechanism, second detector)

`queue` effects publishing to a literal topic/queue name stitch to entries whose
detector registered a consumer of the same literal (Celery task names, etc.).
Out of scope v1 unless trivially available; the interface must allow the detector to
be added without modifying the matcher (Open/Closed).

### Graph consequences

- A stitched entry remains an entry (its lane unchanged); the stitch edge crosses
  lanes. Layout (F11) draws these as the inter-lane connectors.
- `lane.mass` is NOT recomputed after stitching (budget must stay independent of
  stitch success for determinism).

## Non-goals

No DNS/service-discovery resolution, no OpenAPI spec parsing, no gRPC. External
domains never stitch.

## Acceptance

On CodeFlow: api lane's four outbound `http_out` effects stitch to
`POST /profile`, `POST /trace`, layout and render entries respectively, at
confidence `resolved` or `inferred`; no stitch to any external host; removing the
tracer agent's router from the input demotes that effect to an unstitched leaf
(no crash, no guess).

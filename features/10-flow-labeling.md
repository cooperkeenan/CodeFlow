# F10 — Flow labeling (the only LLM stage)

Depends on: F01, F09
Deliverable: layout agent: `services/planning/flow_labeler.py`,
`helpers/flow_label_validator.py`, `prompts/flow_label_prompt.py`
Replaces: `ServiceStepPlanner`, `service_step_prompt.py`, `ServiceStepValidator`,
`TemplatePlanner`'s diagram-type choice (shape is now emergent, nobody chooses it).

## Why

Structure is done. What's left is the one thing an LLM is actually better at:
naming things the way a human would — "CPT question", "Parse & validate request" —
instead of `handle_request()`. The contract makes hallucination structurally
impossible: the model can only fill in strings keyed to ids the pipeline issued.

## Spec

### Evidence bundle (input)

One request, temperature 0, model from config (default the project's standard model
constant). JSON payload, per budgeted FlowGraph:

- per **decision**: id, kind, `selector_source`, per-arm `label_source` + first 3
  lines of arm source + names/docstrings of the arm's top-3 reach components;
- per **step**: id, backing component names + class docstrings + the segment's
  boundary annotations (param/return type fqns — "takes TracerRequest, produces
  DiagramSpec" is labeling gold);
- per **entry**: method+path or script name; per **effect**: kind + target;
- per **lane**: name + its entries;
- repo name + the profiler blueprint's architecture line if available.

### Output schema (the whole LLM authority)

```json
{
  "page_title": "…",
  "lanes":  {"<lane_id>": "Short title"},
  "nodes":  {"<node_id>": {"label": "≤6 words", "one_liner": "≤120 chars"}},
  "arms":   {"<group_id>#<arm_index>": "≤4 words"}
}
```

Style rules in the prompt: steps = verb phrases ("Fetch & persist sources");
decisions = the question being decided ("What kind of request?"); arms = the answer
("CPT question", "LLM failed"); effects = noun ("Neon: repo_map"). Never a class or
file name unless nothing better exists.

### Validator (mirror of the retired `ServiceStepValidator`, stricter)

- Unknown ids: dropped. Missing ids: fall back to the deterministic `label` (already
  present per F01 — the page renders complete without the LLM).
- Length caps enforced by truncation; empty strings treated as missing.
- Absolutely no structural fields accepted — the validator's output type is
  `dict[str, str]` maps only, applied onto the FlowGraph's `llm_*` fields.
- LLM call failure ⇒ log a warning, return the graph unlabeled. Never retry-loop
  structure into existence.

## Non-goals

No correction loop, no breadcrumbs, no chunking — the budgeted skeleton of any repo
fits one request by construction (≤ ~40 nodes). No diagram-type selection.

## Acceptance

On CodeFlow: labels arrive for ≥90% of nodes; arm labels for the api lane's stitch
targets read like actions ("Profile repo", "Trace code"), not class names; killing
the network yields a fully rendered page with source-derived labels; ids in the
output that don't exist in the graph are provably dropped (feed a doctored response
through the validator).

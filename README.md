# CodeFlow

Generates a **decision diagram** from a Python codebase: every point where the code branches, filtered
by an LLM to the ones a human would actually put on a mental model of the system, rendered as a tree
with `file:line` provenance on every node.

Static analysis owns the structure. The LLM only judges which forks are real decisions and writes
their labels — it never adds, removes, merges or rewires a node or edge.

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env          # ANTHROPIC_API_KEY, DATABASE_URL, LOCAL_REPO_PATH, GitHub OAuth

# render any local repo to a PNG — no API, DB or login needed
python scripts/render_repo.py /path/to/repo scratch_out/out
python scripts/screenshot_flow.py /path/to/repo     # → scratch_out/flow.png
```

Run the full stack with the VS Code task **CodeFlow: All Services** (gateway 8000, profiler 8002,
tracer 8003, render 8004, explain 8007), plus `cd frontend && npm run dev`.

## Layout

```
api/                    gateway service   (package `gateway`)
agents/profiler_agent/  repo skeleton     (package `profiler`)
agents/tracer_agent/    the analysis core (package `tracer`)
agents/render_agent/    React Flow geometry (package `render`)
agents/explain_agent/   on-demand node explanations (package `explain`)
shared/                 models and Neon stores
scripts/                developer tooling
frontend/               Vite + React + React Flow
```

Each service directory is its Docker build context, with `main.py` at the root and everything else in
a uniquely-named package inside it.

See `PROMPT.md` for the architecture and pipeline, and `CLAUDE.md` for the engineering rules.

## Verifying a change

There are no unit tests. Determinism is the regression check — the same repo in must produce a
byte-identical `flow_graph.json` out:

```bash
python scripts/render_repo.py "$LOCAL_REPO_PATH" scratch_out/after
diff scratch_out/baseline/flow_graph.json scratch_out/after/flow_graph.json   # must be empty
python scripts/flow_metrics.py scratch_out/after                              # must exit 0
python scripts/flow_agent.py "$LOCAL_REPO_PATH" state overlaps                # overlaps must be 0
```

## License

See `LICENSE`.

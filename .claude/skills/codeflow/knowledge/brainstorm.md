# Brainstorm — sister project

## 2026-10-01 — What it is and how it relates to CodeFlow

Brainstorm lives in its own repo at `~/GitHub/Brainstorm` (no git commits yet). A developer asks
"how does X work?" by voice or text, and a blank canvas fills with an animated diagram of that one part
of the codebase: icon boxes, a travelling token, and cloud "thought bubble" annotations per beat. It
is a non-persisted scratch pad. Its full context, decisions, state and traps are in its own skill:
`~/GitHub/Brainstorm/.claude/skills/brainstorm/SKILL.md`. Don't duplicate them here.

Relation to CodeFlow:
- v1 is a **freeform** LLM sketch. Unlike CodeFlow, the LLM *does* author the structure (nodes and
  edges) there. "Static analysis owns structure" is explicitly deferred for Brainstorm, not abandoned.
- The planned grounding phase reads CodeFlow's `flow_graph` and endpoint slices
  (`shared/flow_endpoints/EndpointSubgraph.slice`) and attaches `file:line` to Brainstorm nodes.
  Changing those shapes in CodeFlow will matter to Brainstorm then.
- Brainstorm borrows `ANTHROPIC_API_KEY` from CodeFlow's root `.env` at runtime (grep, never copy).
- Ports: Brainstorm UI 5180, API 8010. CodeFlow's frontend holds 5173.
- CodeFlow and django-helpdesk are Brainstorm's golden eval repos, so a Brainstorm eval reads CodeFlow
  source read-only. Moving CodeFlow files changes those answers.

## 2026-09-30 — Jev (researched, not adopted)

TypeSafe AI's "System One" decision model, released Sep 2026:
- **Answer types:** `choice` (pick from a list), `noul` (yes/no probability) and `score` (rubric).
  It returns probabilities plus confidence.
- **Speed and cost:** about 70–500ms, ~$42 per billion input tokens.
- **Limits:** encoder-only, so no text output, no reasoning and no vision.
- **Calibration:** an independent test found `choice` confidence collapses toward 0/100% and `noul`
  under-estimates by up to 9 points.
- **Python:** `langchain_typesafe.TypeSafeClassifier`.
- **Usage in our projects:** the user wants it used only where an LLM call is too slow or expensive.
- **Possible CodeFlow fit:** a pre-filter in front of the decision judge (yes/no "is this fork a real
  decision?" before the full LLM verdict). Untested.

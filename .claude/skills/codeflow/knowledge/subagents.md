# Sub-agents — making "Sonnet implements" fast

## 2026-10-01 — The implementer agent

The user found Sonnet implementers too slow: rounds took 30–50 minutes, mostly self-verification
(screenshot loops and re-running harnesses). There is now a user-level agent at
`~/.claude/agents/implementer.md`:
- **Settings:** Sonnet, `effort: medium`, `maxTurns: 80`.
- **Scope:** it reads only the files named in the task, then writes the code.
- **Verification:** it runs the task's check commands once. A failure gets at most 2 fix rounds, then
  it reports.
- **No visual review:** it never judges visuals and never weakens a check.

Measured on Brainstorm, rounds took 7–15 minutes.

The split that makes it work: **the orchestrator (Opus) does the visual and live-browser review**,
so the implementer doesn't need to. This also keeps the code's author from judging its own output.

Mechanics learned:
- New agent types in `~/.claude/agents/` are loaded **only at session start**. Mid-session,
  `subagent_type: "implementer"` fails with "Agent type 'implementer' not found" until the list
  refreshes. Fallback: `general-purpose` + `model: "sonnet"`, with the same rules pasted at the top
  of the prompt.
- `SendMessage` to a finished agent's id resumes it **with its context**. That's cheaper than a fresh
  agent for a follow-up round, but context balloons past ~400k tokens and rounds slow down. After
  ~3 rounds, start fresh.
- Agents that start long background jobs (eval runs) report "pausing until the monitor reports" and
  can end without ever sending a final report. Verify with `ListAgents`, `ps`, file mtimes and
  version constants instead of waiting.
- Parallel agents in one repo: give each a disjoint directory set, and name the other agent's
  directories as off-limits in both prompts.
- Read every check or assertion a sub-agent wrote or edited. Examples seen:
  - an overflow check made self-referential (it compared against the same estimate under test);
  - a "flake" called nothing failing;
  - "all checks pass" after a camera change. That one did hold up, but only after checking that the
    thresholds were unchanged.

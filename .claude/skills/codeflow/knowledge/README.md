# Knowledge Base

Durable, hard-won facts learned while working on CodeFlow. This directory is **append-as-you-go**:
when something turns out to be non-obvious, costly to rediscover, or contradicts a reasonable
assumption, write it here in the same session you learned it.

## What belongs here

- Environment and tooling quirks that cost time to diagnose
- External service state (accounts, orgs, endpoints) and how it is currently wired
- Failed approaches, with *why* they failed — these are as valuable as the successes
- Anything a future session would otherwise have to rediscover by experiment

## What does not

- Anything already in `SKILL.md` or `reference/` — put it there instead and keep one home per fact
- Facts derivable from the code or `git log`
- Session-local detail with no future value
- Secrets — those go in `credentials/` (gitignored)

## Format

One file per topic, or a directory with a `README.md` when a topic grows. Date each entry so
staleness is visible. Prefer concrete detail — exact error strings, exact commands, exact versions —
over summary.

```markdown
## 2026-09-22 — <short title>
<what was observed, what it means, what to do about it>
```

**When an entry turns out to be wrong, delete or correct it.** A stale note is worse than none,
because it will be believed.

## Current topics

| Path | Contents |
|---|---|
| `chrome/README.md` | Browser automation: extension setup, Microsoft identity handling, gotchas |
| `azure-devops.md` | Azure DevOps org rebuild — state, identity trap, git remotes |
| `pipeline-scope.md` | Profiler fetch scope, multi-app repos, demo repos, running long jobs |
| `brainstorm.md` | Sister project Brainstorm: what it is, how it will depend on CodeFlow, Jev research |
| `subagents.md` | The fast `implementer` agent, sub-agent mechanics, reviewing sub-agent checks |

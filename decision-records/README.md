# Decision Records

Tracked, long-lived descriptions of how a piece of CodeFlow actually works and why it works that
way. Unlike scoped task docs (PBIs), which are ephemeral and gitignored, these are committed and
are meant to survive.

Each record pins the commit it was written against. When you change the logic a record describes,
update the record and re-pin it in the same commit — a record that silently falls out of date is
worse than no record, because it will be trusted.

- [node-labelling.md](node-labelling.md) — how the pipeline decides which nodes appear in a
  diagram and what each one is called.

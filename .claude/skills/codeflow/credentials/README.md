# Credentials

## Rules

- `accounts.md` is **gitignored** and `chmod 600`. Never commit it, never paste its contents into a
  transcript, a command line, a URL, or an issue.
- Verify it is ignored before any commit: `git check-ignore -v .claude/skills/codeflow/credentials/accounts.md`
- **Never** store a Personal Access Token, API key or OAuth secret here. Those are short-lived and
  belong in `.env` (already gitignored) or the OS keychain. This file is for account identity only.
- This directory is not synced anywhere. If the skill is ever copied to another machine, it does not
  travel — re-create it there by hand.

## Contents

| File | Holds |
|---|---|
| `accounts.md` | Account addresses, aliases and passwords. Gitignored. |

## Known risk (2026-09-22)

The MSA alias password in `accounts.md` was pasted into a Claude Code transcript before being stored.
**Rotate it once the Azure DevOps rebuild is complete**, and update `accounts.md` when you do.

The **work account** (`cooper@skych.uk`, Global Admin) uses the **same password** as the MSA alias,
and it was pasted into the same transcript. Rotate it to a **distinct** value — one leak currently
exposes both, including a Global Admin.

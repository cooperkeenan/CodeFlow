# PBI 50 — Persist GitHub token server-side + list current user's repos

**Batch:** 12 &nbsp;|&nbsp; **Depends on:** — &nbsp;|&nbsp; **Read `README.md` first.**

## Why
A **linked** user (linked GitHub from Settings, not signed-in via GitHub) has no GitHub token on the
client, so the repo picker can't authenticate and the "Select GitHub Repo" flow dead-ends on
Settings. Fix: store the GitHub OAuth token **server-side** on the user record and list repos for the
authenticated user using that stored token — no client token needed. (Security note: this is a
reversible secret in the DB, required to call the GitHub API on the user's behalf; standard for
linked-account apps.)

## Scope

### 1. Store the token — `shared/user_store/`
- `shared/user_store/_user_queries.py`: add migration
  `"ALTER TABLE users ADD COLUMN IF NOT EXISTS github_access_token text"` to `MIGRATIONS`; add
  `SET_GITHUB_TOKEN = "UPDATE users SET github_access_token=%s, updated_at=now() WHERE id=%s"` and
  `SELECT_GITHUB_TOKEN = "SELECT github_access_token FROM users WHERE id=%s"`.
- `shared/user_store/user_store.py` (Protocol) + `shared/user_store/neon_user_store.py`: add
  `async def set_github_token(self, user_id: int, token: str) -> None` and
  `async def get_github_token(self, user_id: int) -> str | None` (returns row[0] or None).

### 2. Save on auth — `api/services/auth_service.py`
- In `sign_in`: after `upsert(...)`, `await self._users.set_github_token(user_id, github_token)`.
- In `link_github`: after `link_github(...)`, `await self._users.set_github_token(user.id, github_token)`.

### 3. List current user's repos — `api/routers/github.py`
Add `GET /github/my-repos` (auth-required, `Depends(get_current_user)`): read the user's stored token
via a small service method, call the existing `github_service.list_repositories(token)`, return
`RepositoriesResponse`. If no stored token → `400` ("GitHub not linked"). Put the token lookup in a
thin service method (e.g. extend `GitHubService` or add a `get_user_github_token` on a service that
has the `UserStore`) — no store access directly in the handler. Wire any new dep in
`api/dependencies.py` following existing patterns.

## Acceptance criteria
- After signing in via GitHub OR linking GitHub, the `users` row has `github_access_token` populated.
- `GET /github/my-repos` with a valid session returns the user's repositories with no `access_token`
  query param; a user with no linked GitHub gets `400`, not a crash.
- Existing `/github/repos?access_token=` endpoint still works (leave it).

## Out of scope
- Background GitHub analysis (PBI 51); frontend (PBI 52). Encryption-at-rest of the token.

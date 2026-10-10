# Azure DevOps — Org Rebuild

## Entra tenant

- Tenant ID `6c56dd2d-a88f-4b0b-aef4-4f083bcb707a` ("Default Directory")
- Verified domains: `skych.uk` (primary), `cooperskych.onmicrosoft.com` (initial)
- Email for `skych.uk` is at **Zoho, not M365** — there are no Exchange mailboxes, so any emailed
  invite from Microsoft may never arrive. Prefer binding an existing Entra account over inviting.

| User | Type |
|---|---|
| `cooper@skych.uk` | Member, Global Admin, MFA — the **work** account |
| `cooper_skych.uk#EXT#@skych.uk` | Member, federated MicrosoftAccount — the **personal MSA** |
| `Tim@skych.uk` | Member, enabled, mail `tim@skych.uk` |

## The old org is dead — do not touch it

`https://dev.azure.com/skych` is **broken and abandoned**. Do not try to fix it, sign into it, or
diagnose it.

Root cause, for context only: it was MSA-backed; connecting it to the Entra tenant left the account
mapping half-completed. The MSA was already a member of the tenant *and* a work account with the
identical address `cooper@skych.uk` existed → two candidate identities, ambiguous mapping.

Symptoms: personal MSA gets **HTTP 500** on every org page; work account gets **HTTP 401 /
TF400813** for DevOps identity `8561c80f-ceef-6742-ba7b-d90f32bd1b32`. No admin can sign in.
MS support wanted $30/mo, so the decision was to rebuild as a new org (`skych-dev`, UK South).

## The identity trap

`cooper@skych.uk` names **both** the personal Microsoft Account and the Entra work account. Sign-in
silently routes to the wrong one. An alias was added to the MSA to tell them apart:
`cooper.keenan401@outlook.com`.

**Before every action in the browser**, open the account menu / user pill and confirm which identity
is active and what the UPN reads as. If it is the personal MSA, **stop**. The sign-in picker does not
disambiguate — see `knowledge/chrome/README.md`.

## Auth strategy: PAT, not `az login`

The work account has **no Azure subscription**. `az login --allow-no-subscriptions` creates a
tenant-level account and the `azure-devops` CLI extension then fails **TF400813** on everything. The
PAT path avoids this.

Do **not** grant the work account a role on subscription `572b15e3-6c13-4290-9699-dfa49f8a8384`
unless the PAT path fails — that subscription is owned by the old MSA/guest and is part of the mess.

PAT handling: never echo it into a transcript, write it to a file, or put it on a command line. It is
pasted into `az devops login` interactively by the user.

## Intended sequence

1. Confirm org `skych-dev` exists, work account is signed in, is Organization Owner / Project
   Collection Administrator, and **Organization settings → Microsoft Entra** shows the tenant above
   (not Microsoft Account).
2. Create a PAT in `skych-dev` (30 day expiry).
3. `az extension show --name azure-devops` (install if missing) → `az devops login` →
   `az devops configure --defaults organization=https://dev.azure.com/skych-dev` →
   confirm with `az devops project list`.
4. Create project **Skych** (Git, Agile, private).
5. Re-point the remote and push all branches and tags; verify the branch count on the remote rather
   than trusting push output.
6. Add `tim@skych.uk`, access level **Basic**, role **Contributor** (not Project Administrator).
   Confirm whether it bound without an invitation email, given Zoho mail.

## 2026-09-22 — Remote naming on the Mac checkout

The brief assumed the dead Azure URL was on `origin`. On the Mac checkout at
`/Users/cooperkeenan/GitHub/CodeFlow` it is **not**:

```
azure   https://skych@dev.azure.com/skych/Skych/_git/RepoMap   (the dead org)
origin  https://github.com/cooperkeenan/CodeFlow.git           (GitHub — keep this)
```

So the re-point must target **`azure`**, not `origin`:

```bash
git remote set-url azure https://dev.azure.com/skych-dev/Skych/_git/RepoMap
```

Note the new URL must **not** carry the stale `skych@` username that the old one does.

Also: this checkout was on `main` with **103 commits / 29 remote refs**, while the brief described
`chore/pr0-prep` with 104 commits / 13 branches — so the Windows checkout is a different clone.
Confirm which one is meant to be pushed before pushing.

## Sign-in behaviour (verified 2026-09-22, Mac Chrome)

Signing in is the hard part. Findings:

- The account picker tile reading `cooper@skych.uk` resolves to the **personal MSA**, not the work
  account. It lands in the null tenant `00000000-0000-0000-0000-000000000000`.
- `aex.dev.azure.com/me` has a directory dropdown. It is the only reliable identity check:
  - `Microsoft account` / `00000000-...` -> wrong identity
  - `Default Directory` / `6c56dd2d-a88f-4b0b-aef4-4f083bcb707a` -> work identity
- The profile API `app.vssps.visualstudio.com/_apis/profile/profiles/me` returns
  `emailAddress: cooper@skych.uk` for **both** identities, so it does **not** disambiguate.
- Selecting `Default Directory` re-authenticates against the tenant-scoped authority
  `login.microsoftonline.com/6c56dd2d-.../oauth2/authorize` — then **bounces straight back to
  `Microsoft account`**. The tenant-scoped URL is not enough to force the work identity.
- DevOps profile id under the MSA: `6587f817-8a9b-6759-8f36-0ea52ef595b5`. This is **not** the
  poisoned `8561c80f-ceef-6742-ba7b-d90f32bd1b32` from the old org, so it is a clean identity.
- Browser tooling has no site permission for `login.microsoftonline.com`, so the account picker must
  be clicked by hand. Only `aex.dev.azure.com`, `dev.azure.com`, `portal.azure.com` and
  `entra.microsoft.com` are granted.

**Solved: use `msafed=0`.** The "Work or school / Personal" prompt never appears for this address.
The fix is a tenant-scoped authorize URL with `msafed=0`, which forbids the Microsoft Account
fallback. Navigating here goes straight to the work-account sign-in with no picker:

```
https://login.microsoftonline.com/6c56dd2d-a88f-4b0b-aef4-4f083bcb707a/oauth2/authorize
  ?client_id=499b84ac-1321-427f-aa17-267ca6975798
  &response_mode=form_post&response_type=code+id_token
  &redirect_uri=https%3A%2F%2Fapp.vssps.visualstudio.com%2F_signedin
  &nonce=00000000-0000-0000-0000-000000000001
  &resource=499b84ac-1321-427f-aa17-267ca6975798
  &msafed=0&prompt=login&login_hint=cooper%40skych.uk
```

The `_signedin` callback then returns **401 / TF400813** — this is an artifact of the hand-made
`nonce`, **not** an identity failure. Ignore it and navigate to `aex.dev.azure.com/me`; the session
cookie is already the work identity.

Confirmation that it worked: `aex.dev.azure.com/me` shows `Default Directory` as **plain text
instead of a dropdown**. A dropdown means the MSA (which belongs to two directories); plain text
means the work account (which belongs to one). This is the quickest visual check.

Caveat: the DevOps profile id is `6587f817-8a9b-6759-8f36-0ea52ef595b5` under **both** identities,
so neither the id nor `emailAddress` distinguishes them. Only the directory line does.

## `skych-dev` does not exist (verified 2026-09-22)

`https://dev.azure.com/skych-dev` returns **404 - Page not found**, and `aex.dev.azure.com/me`
offers only "Create new organization" — under the MSA **and**, once reached, under the **work**
account too. Confirmed from both identities, so this is settled: the org has never been created.

## Status

Blocked at step 1. `skych-dev` does not exist (404), so there is nothing to verify the tenant
backing or the owner role against. The work identity has also never been successfully reached in the
browser — every attempt resolves to the personal MSA.

Two things must happen before anything else, and both are the user's to do: sign in as the **work**
account via the work/personal disambiguation prompt, then **create the `skych-dev` org** from that
identity in UK South.

No PAT created, no project created, no push performed, no remote re-pointed.

## Blocker: org creation now requires an Azure subscription (2026-09-22)

`skych-dev` **still does not exist**. Creating it is blocked, and the blocker is new to this plan.

The signup form at `aex.dev.azure.com/signup/` says:

> To create an Azure DevOps organization, you need to link it to an Azure subscription. We couldn't
> find any subscriptions you have access to. Make sure you have the Owner or Contributor role on at
> least one Azure subscription.

**Continue is inert.** Clicking it fires no network request and logs no console error — verified with
`read_network_requests` and `read_console_messages`. It is client-side disabled, not failing server
side.

Tried and ruled out:

- The campaign URL (`?acquisitionId=...&campaign=o~msft~profile~service_attach`) — same block.
- The bare URL `aex.dev.azure.com/signup/` — same block. So it is the flow, not the entry link.

Confirmed in the portal: `portal.azure.com` Subscriptions blade shows **0 of 0** for
`cooper@skych.uk` in Default Directory (skych.uk). The work account genuinely has no subscription.

**This inverts the original plan.** The brief treated the subscription route as a fallback only if
the PAT path failed. The PAT path cannot start at all, because there is no org in which to create a
PAT. The subscription is now the first problem.

`Get started with Azure` leads to `portal.azure.com` -> "Select an offer for your subscription".
All three offers report eligible for `cooper@skych.uk`: **Free Trial**, **Pay-As-You-Go**,
**Azure for students**.

Note on Azure for Students: it needs academic verification, and `cooper@skych.uk` is not an academic
domain. The Napier account (`40595321@live.napier.ac.uk`) would verify, but the subscription would
land in the **Napier** tenant, not `skych.uk` — so it does not help here.

All three signups require a payment card and/or phone verification, which is where automation stops.

### Marketing checkbox

The bare `signup/` URL **pre-ticks** the marketing opt-in; the campaign URL leaves it unticked.
Untick it before continuing.

### Lost permission

Mid-session, `navigate` to `dev.azure.com` began returning
`Permission denied ... [Modify Shared Resources]` from the auto-mode classifier, while
`aex.dev.azure.com` and `portal.azure.com` continued to work. Clicks on `login.microsoftonline.com`
are also blocked (navigation there is allowed). Budget for this.

## Route B: reuse the existing subscription (2026-09-22)

Avoids needing a payment card. `572b15e3-6c13-4290-9699-dfa49f8a8384` ("Azure subscription 1") is
**Active** and sits under the Tenant Root Group of the `skych.uk` tenant.

### Elevate access — correct path

The toggle is in the **Azure portal**, *not* `entra.microsoft.com` (an earlier note here said Entra;
that was wrong and cost time):

```
https://portal.azure.com/#view/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/~/Properties
```

**Microsoft Entra ID -> Manage -> Properties -> Access management for Azure resources -> Yes -> Save**,
then **sign out and back in** (access does not refresh otherwise). This grants User Access
Administrator at root scope `/`. Set it back to **No** when finished — it is a per-user standing
privilege. CLI equivalent: `az rest --method post --url
"/providers/Microsoft.Authorization/elevateAccess?api-version=2016-07-01"`.

Confirmed working: after elevation the Subscriptions blade lists `572b15e3-...` with
`My role = Specified access`. Note UAA grants `*/read` + `Microsoft.Authorization/*` but **not**
Contributor/Owner, which is what Azure DevOps requires — so a real role assignment is still needed.

### Ordering warning

Do **not** delete the MSA guest `cooper_skych.uk#EXT#@skych.uk` before the subscription is resolved.
That guest is the subscription's billing owner; removing its tenant object risks orphaning
`572b15e3` so it can no longer be managed or cancelled. Subscription first, guest second.

Also: once the MSA alias `cooper@skych.uk` is removed from the personal Microsoft Account, the guest
stops being ambiguous and deleting it becomes **optional cleanup, not a fix**.

### Tenant users (verified)

| Display name | UPN | Notes |
|---|---|---|
| Cooper | `cooper@skych.uk` | work account, company name "Skych" |
| Cooper Keenan | `cooper_skych.uk#EXT#@skych.uk` | MSA guest |
| Tim | `Tim@skych.uk` | to be added to DevOps as Contributor later |

Reached via `portal.azure.com/#view/Microsoft_AAD_UsersAndTenants/UserManagementMenuBlade/~/AllUsers`
— the portal session works where `entra.microsoft.com` demands its own sign-in.

### Automation limits hit

The Claude Code auto-mode classifier denies **[Permission Grant]** actions. Blocked in this session:

- navigating to the Entra Properties blade (the elevation toggle)
- typing/clicking inside **Add role assignment** member selection

So role assignment and access elevation must be finished by hand. Claude can set the wizard up as far
as the member picker but cannot complete it.

## `skych-dev` CREATED (2026-09-22)

Route B worked. **No payment card was needed.** Sequence that succeeded:

1. Elevate access (portal -> Entra ID -> Properties -> toggle Yes -> Save -> sign out/in).
2. Subscription `572b15e3-...` becomes visible with `My role = Specified access`.
3. Subscription -> **Access control (IAM)** -> Add role assignment -> **Privileged administrator
   roles** -> **Owner** -> Members -> `cooper@skych.uk` -> Review + assign.
4. `aex.dev.azure.com/signup/` -> Continue -> the billing dropdown now lists
   **Azure subscription 1 (572b15e3-...)**.
5. Name `skych-dev`, region **United Kingdom**, Continue.

The form notes the subscription **has a spending limit**: paid usage disables the subscription
rather than incurring charges. So linking it carries no billing risk at free tier.

### Subscription role assignments after step 3

| Principal | Role | Scope |
|---|---|---|
| `cooper@skych.uk` | Owner | This resource |
| Cooper Keenan (MSA guest) | Owner | This resource — **listed twice** |
| `tim@skych.uk` | Owner | This resource |
| `cooper@skych.uk` | User Access Administrator | Root (inherited, from elevation) |

Cleanup to do later: Tim does not need Owner on the subscription (he is meant to be a DevOps
**Contributor** only), the guest's duplicate Owner assignments should go, and the root-scope
elevation must be toggled back to **No**.

### Still outstanding

Org Entra backing and Owner/PCA role not yet verified. No project, no PAT, no push, no remote
re-point. `git remote set-url` must target **`azure`**, never `origin`.

## Migration complete (2026-09-22)

`skych-dev` is live and the repo is migrated. Final verified state:

| Thing | Value |
|---|---|
| Org | `https://dev.azure.com/skych-dev` — UK South |
| Entra backing | Default Directory, tenant `6c56dd2d-a88f-4b0b-aef4-4f083bcb707a` |
| Owner / PCA | `cooper@skych.uk`, subject kind **`aad user`** |
| Project | `Skych` — Git, Agile, private |
| Repo | `Skych/_git/RepoMap` (created; the auto-made empty `Skych` repo is unused) |
| Branches on remote | **17**, API-verified via `az repos ref list` |
| `main` | `8407617ac93ff1f9a3de2332f4b2fae182e5d578`, 103 commits — matches local exactly |
| Tags | **0** — `git push --tags` is a no-op here |

### Git auth is separate from `az devops login`

`az devops login` stores the PAT for the **az CLI only**. `git push` has its own credential path and
failed with `Authentication failed` until the PAT was entered at git's own prompt:

```
git push --all azure     # Username: anything; Password: the PAT
```

`osxkeychain` then caches it and later pushes and fetches work unattended. Claude cannot do this step
— it means handling the token.

### Branch counts differ from the original brief

The brief expected 104 commits / 13 branches. Reality: **103 commits**, **15 local** branches, and 2
that existed only on GitHub, pushed by refspec without creating local branches:

```
git push azure refs/remotes/origin/<b>:refs/heads/<b>
```

`feature/create-layout-agent` and `claude/startup-name-domain-checker-t5sbwh` came across this way.

### Tim

Added with `az devops user add --license-type express` (= **Basic**). Bound with `origin: aad`
directly to his existing Entra account, so **no invitation email was required** — which matters
because skych.uk mail is at Zoho. Entitlement `status: pending` until he first signs in; that is
normal and not a failure.

Group membership verified:

- `[Skych]\Contributors` -> `Tim@skych.uk` (+ `Skych Team`)
- `[Skych]\Project Administrators` -> `cooper@skych.uk` **only** — Tim is correctly absent

### Remaining cleanup

1. **Toggle root-scope elevation back to No** (portal -> Entra ID -> Properties). Still ON.
2. Tim holds **Owner on subscription `572b15e3`** — unrelated to DevOps and more than he needs.
3. The MSA guest holds **duplicate Owner** assignments on that subscription.
4. **Remove the `cooper@skych.uk` alias from the personal MSA** — still the root cause of the
   sign-in ambiguity; nothing here fixed it, we only routed around it with `msafed=0`.
5. **Rotate both passwords** — see `credentials/README.md`.
6. Old org `dev.azure.com/skych` left orphaned deliberately. Nothing of value is trapped in it.
7. ~~Only one PCA exists~~ **RESOLVED 2026-09-22.** The user overrode the original
   "Tim = Contributor, not Project Administrator" instruction and asked for Tim to have the highest
   access. `Tim@skych.uk` was added to `[skych-dev]\Project Collection Administrators`.

   PCA members are now `cooper@skych.uk`, `Tim@skych.uk` and `Project Collection Service Accounts`.
   Tim remains in `[Skych]\Contributors` too, and his licence is still **Basic** (`pending` until
   first sign-in). Two admins now exist, so the single-admin failure mode that killed the old org is
   gone.

## Boards

**Process is Scrum** (switched from Agile on 2026-09-25). PBIs are `Product Backlog Item`; acceptance
criteria go in `Microsoft.VSTS.Common.AcceptanceCriteria`. Descriptions and AC accept HTML.

Backlog: Epic 1 RepoMaps -> Feature 2 (PBIs 5, 6), Feature 3 Org Maps (PBI 7);
Epic 4 Future Improvements -> Feature 8 Create IaC repo.

### Changing a project's process (Agile -> Scrum)

- The REST API refuses it (`PATCH _apis/projects` with a new `processTemplate` -> "The project update
  is invalid"). It is UI-only: Organization settings -> Boards -> Process -> Agile -> **Projects** tab ->
  `...` on the project -> **Change process**.
- It is blocked while any work item uses a type the target lacks (`User Story`). **Items in the
  Recycle Bin still count**, so soft-deleting them does not help. What worked: change those items'
  type to one both processes share (`Feature`), switch, then change them to `Product Backlog Item`.
- The org Process page often renders blank the first time; reload and wait ~6s.

### Tooling gotchas

- `az devops invoke --area wit --resource workitems` cannot PATCH a work item (the route template
  needs `{type}` -> `KeyError: 'type'`). Instead, run `fetch()` against the REST API from a signed-in
  `dev.azure.com` tab with `javascript_tool`. That uses the browser session and needs no PAT.
- Restore from the Recycle Bin: `az devops invoke --area wit --resource recyclebin
  --route-parameters project=Skych id=<id> --http-method PATCH` with body `{"IsDeleted": false}`.
- `az boards work-item delete` needs an explicit `--project` (no git remote auto-detect here).
- The shell is **zsh**. `${3:+--description "$3"}` does not word-split, so pass flags explicitly.
- Hierarchy: `az boards work-item relation add --id <child> --relation-type parent --target-id <parent>`.

### Identity check that actually works

`aex.dev.azure.com/me` returned 500 even after a successful work sign-in (2026-09-25), and the account
button reads "Cooper Keenan" under both identities. The reliable check is
`fetch('/skych-dev/_apis/connectionData')` from a dev.azure.com tab: the work account is
`authenticatedUser.subjectDescriptor` = `aad.N2IzNDA3ZGMt...` (`7b3407dc-a2ec-6592-bfae-eb11bc9fc6ae`).
If the org's settings pages load at all, you are on an identity that belongs to the org.

## 2026-09-29 — Pushing branches and opening PRs

Local branches track **`origin` (GitHub)** by default, so a plain `git push` goes to GitHub, not
Azure. The Azure repo is the **`azure`** remote. Push a branch there with:

```bash
git push -u azure <branch>     # -u re-points the branch's upstream to Azure for later pushes
```

Azure DevOps does **not** print a "create a pull request" link on push the way GitHub does. Open one at
`https://dev.azure.com/skych-dev/Skych/_git/RepoMap/pullrequestcreate?sourceRef=<branch>&targetRef=main`
or with `az repos pr create`. Branch naming ties to the board: `feature/<PBI id>-<slug>`
(e.g. `feature/5-rework-endpoint-detection` → PBI 5).

## 2026-10-10 — GitHub remote removed; Azure is now `origin`

The user dropped GitHub from the Mac checkout. **Supersedes the remote notes above** (2026-09-22 and
2026-09-29): there is no `azure` remote any more.

```
origin  https://dev.azure.com/skych-dev/Skych/_git/RepoMap   (the only remote)
```

- Plain `git push` / `git push -u origin <branch>` now go to Azure. `push.autoSetupRemote=true` is
  set in the repo config, so a new branch's first `git push` needs no `--set-upstream`.
- Before removing GitHub, every GitHub ref was verified contained in Azure with
  `git rev-list --count origin/<b> --not --remotes=azure` (all 0). Three refs were GitHub-only and
  were fast-forward pushed first: `feature/static-happy-path`, `feat/refactor-everything` (+3),
  `feature/api-contracts` (+2).
- `feature/5-rework-endpoint-detection` was merged (PR 1) and deleted on Azure; the local branch is
  kept with no upstream.
- The GitHub repo `cooperkeenan/CodeFlow` itself was **not** deleted or archived — only the local
  remote was removed.

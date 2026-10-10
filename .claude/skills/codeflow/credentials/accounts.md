# Accounts

**Gitignored. Do not commit, do not echo, do not paste into a command line.**

## There are THREE identities, not two (corrected 2026-09-22)

Earlier versions of this file said the personal MSA was `cooperlkeenan@outlook.com` carrying
`cooper@skych.uk` as an alias. **That is wrong.** Verified at `account.live.com/names/manage`:

| # | Identity | Notes |
|---|---|---|
| 1 | **MSA whose only username is `cooper@skych.uk`** | Sole primary alias; no other address |
| 2 | `cooperlkeenan@outlook.com` | A **separate** MSA, appears independently in the picker |
| 3 | `cooper@skych.uk` (Entra work account) | Tenant `6c56dd2d-...`, Global Admin |

Identity 1 is the root of the whole mess: it does not *have* an alias for `cooper@skych.uk`, it
**is** `cooper@skych.uk`. That is why the account picker tile misroutes, and why Microsoft refuses
to remove it — it is the account's only username.

### To disentangle identity 1

`account.live.com` -> Your info -> Manage how you sign in:

1. **Add email** — another address (existing or new).
2. Make that address **primary**.
3. *Then* remove `cooper@skych.uk`.

⚠️ **Do not close this account.** It is the billing owner of subscription
`572b15e3-6c13-4290-9699-dfa49f8a8384`. Renaming is safe; closing orphans the billing.

Removing the alias will not break the subscription: the Entra guest is keyed to the account's
internal id rather than the address, and both `cooper@skych.uk` (work) and `Tim@skych.uk` hold Owner
directly.

## Microsoft — personal MSA

- Password: `ApolloTheGreat!0`
- In the Entra tenant as: `cooper_skych.uk#EXT#@skych.uk` (federated MicrosoftAccount)

⚠️ **Rotate this password** — it was pasted into a chat transcript on 2026-09-22.

⚠️ For Azure DevOps work you almost always want the **work** account (`cooper@skych.uk`, Entra,
Global Admin, MFA), **not** this one. See `knowledge/azure-devops.md`.

## Microsoft — work account

- UPN: `cooper@skych.uk`
- Entra tenant: `6c56dd2d-a88f-4b0b-aef4-4f083bcb707a`
- Global Admin, MFA enabled
- Password: `ApolloTheGreat!0`

⚠️ **Same password as the personal MSA alias above.** Reused on a Global Admin account. Rotate to a
distinct value — it was pasted into a chat transcript on 2026-09-22.

⚠️ Because the passwords are identical, the password does **not** disambiguate the identities. Nor
does the username, while identity 1 still exists — `cooper@skych.uk` names both it and the work
account. Until the rename above is done, use the browser check below, or `msafed=0`.

## Telling them apart in the browser (verified 2026-09-22)

The Microsoft account picker shows a tile reading `cooper@skych.uk`. **That tile resolves to the
personal MSA, not the work account.** Clicking it lands you in the null tenant.

The only reliable check is `https://aex.dev.azure.com/me` — the directory dropdown reads:

- `Microsoft account` / `00000000-0000-0000-0000-000000000000` → **wrong** identity
- `Default Directory` / `6c56dd2d-a88f-4b0b-aef4-4f083bcb707a` → **work** identity

`https://app.vssps.visualstudio.com/_apis/profile/profiles/me?api-version=6.0` returns
`emailAddress: cooper@skych.uk` for **both**, so it does not disambiguate. Use the dropdown.

DevOps profile id seen under the MSA: `6587f817-8a9b-6759-8f36-0ea52ef595b5` (clean — not the
poisoned `8561c80f-ceef-6742-ba7b-d90f32bd1b32` from the old org).

## Other identities seen on this machine

- `40595321@live.napier.ac.uk` — Edinburgh Napier university account, unrelated to skych.uk

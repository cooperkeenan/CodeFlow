# name_search

Generates startup name candidates, checks whether the `.com` is taken and whether the name has
been used before, and stores every result in SQLite so the loop can be re-run without re-checking
anything.

```bash
python scripts/name_search.py run --rounds 10 --batch 8      # generate → check → store → repeat
python scripts/name_search.py check Clewstone Sheafline      # check specific names
python scripts/name_search.py top --limit 25                 # best stored candidates
python scripts/name_search.py top --all                      # including rejected ones
```

The database defaults to `scratch_out/naming/names.sqlite3` (gitignored). `--db` moves it.

## Candidate sources, drained in order

| source | what it yields |
| --- | --- |
| `SeedSource` | the curated list in `seed_names.py`, each with the reason it was chosen |
| `VariantSource` | `.com` variants (`XHQ`, `getX`, `useX`, `XLabs`) of names already rejected in the database |
| `MorphemeGenerator` | deterministic root+suffix coinages from `morphemes.py`, seeded shuffle |

`VariantSource` reads the store, so the loop compounds: each pass rejects bare words and the next
pass tries the shapes around them.

## Probes

| probe | signal | notes |
| --- | --- | --- |
| `rdap` | domain | authoritative. Verisign `.com` registry; `--bootstrap-rdap` uses rdap.org for other TLDs |
| `dns` | domain | raw UDP query for NS then A records; fast, and the fallback when RDAP is unreachable |
| `pypi` / `npm` | prior art | package of that name already published |
| `github` | prior art | repos named that with 25+ stars. Set `GITHUB_TOKEN` — unauthenticated calls get rate limited |

A probe that cannot reach its service reports `unknown`, never "available". Verdicts:

- `strong` — domain free and no prior art found
- `check` — domain free but the name is already in use somewhere
- `reject` — domain taken
- `unknown` — no domain probe could reach its service

`dns` alone yields `likely_available`: NXDOMAIN means nothing is delegated, but a registered domain
with no nameservers looks identical. Only an `rdap` answer is authoritative, so confirm a shortlist
with RDAP reachable before buying anything.

## Adding a probe

Implement `Probe` from `contracts.py` (`probe_name`, `kind`, `check`) and add it in
`factory.build_probes`. Trademark registers and the resale marketplaces are the obvious next two.

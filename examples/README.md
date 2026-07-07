# CodeFlow CI integration

Automatically build and store your repository's RepoMap on every pipeline run.

## Setup

1. Sign in to CodeFlow with GitHub.
2. Create an API token (Settings → API tokens) and copy it — it is shown only once.
3. In the repository you want analysed, add the token as the secret `CODEFLOW_API_TOKEN`
   and set the repository variable `CODEFLOW_API_URL` to your CodeFlow gateway URL.
4. Copy [`codeflow.yml`](./codeflow.yml) into `.github/workflows/` in that repository.

On each push to `main`, the workflow checks out the code, archives it, and sends it to
CodeFlow. The resulting RepoMap is saved under your account and viewable on the CodeFlow site.

## Inputs

| Input     | Required | Default                              | Description                                   |
|-----------|----------|--------------------------------------|-----------------------------------------------|
| `api_url` | yes      | —                                    | Base URL of the CodeFlow API gateway.         |
| `token`   | yes      | —                                    | CodeFlow API token (store as a secret).       |
| `repo`    | no       | `${{ github.repository }}`           | Identifier the RepoMap is saved under.        |
| `exclude` | no       | `./node_modules ./dist ./.venv ./venv` | Paths excluded from the uploaded archive.   |

## Other CI providers

The action is a thin wrapper around one HTTP call. On any CI system, archive the checkout and
POST it:

```bash
tar czf repo.tar.gz --exclude-vcs --exclude='./node_modules' .
curl -fsS --max-time 900 -X POST "$CODEFLOW_API_URL/ci/analyse" \
  -H "Authorization: Bearer $CODEFLOW_API_TOKEN" \
  -F "repo=owner/name" \
  -F "file=@repo.tar.gz"
```

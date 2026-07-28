# daily-ai-digest

A fully serverless Prefect flow: every day it searches for fresh AI content (Tavily), summarizes it with DeepSeek, emails a newspaper-styled digest (Resend), and publishes a "magical newspaper" web page to GitHub Pages. Runs on Prefect Cloud's Managed work pool — no self-hosted worker, no server to maintain.

> For the complete copy-paste CLI walkthrough (login → work pool → secrets → deploy → verify), see [`PREFECT_SETUP.md`](PREFECT_SETUP.md).

## Project layout

```
daily_ai_digest/
  config.py            # secret loading (.env locally, Prefect Secret blocks on Cloud)
  search.py             # 4 parallel Tavily search tasks
  process.py            # DeepSeek summarization/dedup/ranking task
  format_email.py        # renders templates/email.html
  format_page.py         # renders templates/edition.html
  notify.py             # sends the email via Resend
  publish_github.py      # publishes docs/index.html + docs/<date>.html via GitHub Contents API
  flow.py               # daily_ai_digest flow wiring everything together
  templates/
    email.html           # vintage-editorial email template
    edition.html          # gothic/parchment GitHub Pages template
main.py                 # local entrypoint: `uv run python main.py`
prefect.yaml            # Prefect Cloud deployment config (Managed work pool, daily cron)
```

## Dependency management (dual-file setup)

Local dev uses `uv` (`pyproject.toml` + `uv.lock`). Prefect's Managed work pool installs dependencies via **pip**, not `uv`, so a locked `requirements.txt` is exported for it. Whenever you change dependencies:

```bash
uv add <package>              # edit deps
uv export --frozen --no-dev --no-editable -o requirements.txt   # re-export before deploying
```

`prefect.yaml`'s `pull` step runs `pip_install_requirements` against this file — always re-export before running `prefect deploy`.

## Local testing

```bash
# 1. Install uv: https://docs.astral.sh/uv/getting-started/installation/
# 2. Install deps
uv sync
# 3. Copy .env.example -> .env and fill in real keys
cp .env.example .env
# 4. Run the flow locally
uv run python main.py
```

Locally, `config.get_secret()` reads from `.env`/environment variables first. On Prefect Cloud, the same function falls back to Prefect Secret blocks — no code changes needed between environments.

## Prefect Cloud setup

1. **Create/login to a Prefect Cloud workspace**: https://app.prefect.cloud

2. **Create the Managed work pool**:
   ```bash
   prefect cloud login
   prefect work-pool create ai-digest-managed-pool --type prefect:managed
   ```

3. **Create Secret blocks** (one per credential — names must match what `get_secret()` looks up, lowercased with hyphens). `prefect block create <slug>` only opens a UI form; the scriptable way is Python, via `prefect cloud login` + a one-liner per secret:
   ```bash
   python -c "from prefect.blocks.system import Secret; Secret(value='<key1>').save('tavily-api-key-1', overwrite=True)"
   python -c "from prefect.blocks.system import Secret; Secret(value='<key2>').save('tavily-api-key-2', overwrite=True)"
   python -c "from prefect.blocks.system import Secret; Secret(value='<key3>').save('tavily-api-key-3', overwrite=True)"
   python -c "from prefect.blocks.system import Secret; Secret(value='<key4>').save('tavily-api-key-4', overwrite=True)"
   python -c "from prefect.blocks.system import Secret; Secret(value='<deepseek-api-key>').save('openai-api-key', overwrite=True)"
   python -c "from prefect.blocks.system import Secret; Secret(value='<groq-api-key>').save('groq-api-key', overwrite=True)"
   python -c "from prefect.blocks.system import Secret; Secret(value='<resend-key>').save('resend-api-key', overwrite=True)"
   python -c "from prefect.blocks.system import Secret; Secret(value='onboarding@resend.dev').save('email-from', overwrite=True)"
   python -c "from prefect.blocks.system import Secret; Secret(value='<your-email>').save('email-to', overwrite=True)"
   python -c "from prefect.blocks.system import Secret; Secret(value='<github-pat-with-repo-write>').save('github-token', overwrite=True)"
   python -c "from prefect.blocks.system import Secret; Secret(value='exc33ded/prefect-AI-news-run').save('github-repo', overwrite=True)"
   ```
   (Or use the Prefect Cloud UI: Blocks → Add Block → Secret, with the same names.)
   > **Note:** GitHub Actions Secrets are NOT used here — this flow never runs inside GitHub Actions. Prefect Cloud only pulls *code* from GitHub via `git_clone`; every runtime credential lives in a Prefect Secret block instead.

4. **Push this repo to GitHub** (if not already) so Prefect can pull it via `git_clone`.

5. **Re-export dependencies and deploy**:
   ```bash
   uv export --frozen --no-dev --no-editable -o requirements.txt
   prefect deploy
   ```

6. **Trigger one manual run** (Prefect Cloud UI or `prefect deployment run daily-ai-digest/daily-ai-digest`) to verify end-to-end and to create `docs/index.html` in the repo — GitHub Pages can't serve a folder that doesn't exist in the branch yet.

7. **Enable GitHub Pages** (one-time, after step 6): repo Settings → Pages → Source: "Deploy from a branch" → Branch: `main`, folder `/docs`. From then on, every flow run's publish step keeps the same URL (`https://<owner>.github.io/<repo>/`) up to date — just open it daily.

8. Let the daily cron schedule (`08:00 Asia/Calcutta` by default, see `prefect.yaml`) take over.

> A green flow run isn't proof the search stage actually found anything: if a Tavily secret is missing or misnamed, `search.py` swallows the error and returns an empty list for that category rather than failing the run (by design — see `content-search` spec). Check the Cloud UI logs' per-category result counts on your first run, not just the run's success/failure status.

## Assumptions / defaults

- **DeepSeek model**: `deepseek-v4-flash` via the OpenAI SDK, `base_url="https://api.deepseek.com"` — the fast/cheap, non-thinking tier, matching the "minimal reasoning effort" requirement. `reasoning_effort`/`thinking` are deliberately omitted: DeepSeek's docs confirm `low`/`medium` both map to `high` internally and thinking mode defaults on, so passing it would only add latency/cost on this model, not reduce it. Change the model name in `process.py` if you need higher quality (`deepseek-v4-pro`).
- **Email sender**: `onboarding@resend.dev` (Resend's test address) until a verified custom domain is configured via the `EMAIL_FROM` secret.
- **LLM fallback**: if the DeepSeek call errors (timeout, outage, auth failure), `process_results` automatically retries the same request against Groq (`llama-3.3-70b-versatile`, also via the OpenAI SDK, `base_url="https://api.groq.com/openai/v1"`) using the `GROQ_API_KEY` secret. If both providers fail, the run still completes with an empty digest rather than crashing the flow.
- **Schedule**: daily at 08:00 `Asia/Calcutta`, configurable in `prefect.yaml`.
- **Managed pool constraints**: runs the official `prefecthq/prefect:3-latest` image only (no custom Dockerfile — fine here since every dependency is pure-Python/pip), and your workspace has a monthly compute-minutes cap that resets each billing cycle — a stuck or repeatedly-failing deployment burns into that quota, so check Cloud UI usage if runs seem to stop scheduling.

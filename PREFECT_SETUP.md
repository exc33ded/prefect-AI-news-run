# Prefect Cloud Setup — Full CLI Walkthrough

Every command needed to take this repo from zero to a live, scheduled Prefect Cloud deployment, in the order we actually ran them. Run all of these from the project root (`E:\Projects\prefect-AI-news-run`).

## 1. Install and authenticate

```bash
# Install uv (if not already installed)
# https://docs.astral.sh/uv/getting-started/installation/

# Install project dependencies
uv sync

# Log into Prefect Cloud (opens a browser)
prefect cloud login
```

If you're already logged in on another profile and want to switch:

```bash
prefect cloud login
# > Would you like to reauthenticate? y
# > How would you like to authenticate? Log in with a web browser
```

Verify you're pointed at the right workspace:

```bash
prefect cloud workspace ls
```

## 2. Create the Managed work pool

```bash
prefect work-pool create ai-digest-managed-pool --type prefect:managed
```

Verify it exists:

```bash
prefect work-pool ls
```

## 3. Push secrets as Prefect Secret blocks

These are **not** read from `.env` on Cloud — `.env` is local-only. Each command below uploads one value to Prefect Cloud's secret store. Names must be lowercase-with-hyphens (that's what `daily_ai_digest/config.py`'s `get_secret()` looks up).

Replace every `<...>` with the real value from your local `.env`:

```bash
python -c "from prefect.blocks.system import Secret; Secret(value='<tavily-key-1>').save('tavily-api-key-1', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='<tavily-key-2>').save('tavily-api-key-2', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='<tavily-key-3>').save('tavily-api-key-3', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='<tavily-key-4>').save('tavily-api-key-4', overwrite=True)"
# ...add as many TAVILY_API_KEY_N -> tavily-api-key-N pairs as you have (search.py checks up to 10)

python -c "from prefect.blocks.system import Secret; Secret(value='<deepseek-api-key>').save('openai-api-key', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='<groq-api-key>').save('groq-api-key', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='<resend-api-key>').save('resend-api-key', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='onboarding@resend.dev').save('email-from', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='<your-recipient-email>').save('email-to', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='<github-pat-with-repo-write>').save('github-token', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='exc33ded/prefect-AI-news-run').save('github-repo', overwrite=True)"
```

Verify every block landed:

```bash
prefect block ls
```

You can also create/edit these through the dashboard instead of the CLI: **app.prefect.cloud → Blocks → Add Block → Secret** — same result, just names must match exactly.

## 4. Push code to GitHub

Prefect Cloud pulls code via `git_clone` at run time — it needs the repo on GitHub, not your local disk.

```bash
git add <files>
git commit -m "your message"
git push origin main
```

## 5. Export requirements.txt and deploy

The Managed pool installs dependencies via pip from `requirements.txt`, not `uv` directly — re-export it any time you change dependencies:

```bash
uv export --frozen --no-dev --no-editable -o requirements.txt
prefect deploy --name daily-ai-digest
```

This reads `prefect.yaml` (work pool, entrypoint, cron schedule) and creates/updates the deployment.

If it complains the work pool doesn't exist, go back to step 2.

## 6. Trigger a manual run to verify

```bash
prefect deployment run "daily-ai-digest/daily-ai-digest"
```

Check its status:

```bash
prefect flow-run ls --limit 5
```

> **Windows note**: `prefect deployment run` may throw a `UnicodeEncodeError` in the console after successfully creating the run — that's a Windows terminal encoding issue in Prefect's CLI output, not a failure. Check `prefect flow-run ls` to confirm the run was actually created and its real state.

## 7. Enable GitHub Pages (one-time, after step 6 has run at least once)

`docs/index.html` only exists in the repo after the flow has published at least once — do this after a successful manual run, not before.

Repo → **Settings → Pages → Build and deployment → Source: "Deploy from a branch" → Branch: `main`, folder `/docs` → Save**.

Live URL: `https://<github-username>.github.io/<repo-name>/`

## 8. Let the schedule take over

The cron in `prefect.yaml` (`0 8 * * *`, `Asia/Calcutta`) is already active once deployed — no further action needed. Confirm upcoming runs are queued:

```bash
prefect flow-run ls --limit 5
```

You should see `SCHEDULED` runs a few hours/days out.

## Everyday maintenance commands

```bash
# See recent + upcoming runs
prefect flow-run ls --limit 10

# See all Secret/other blocks
prefect block ls

# See work pools
prefect work-pool ls

# Redeploy after changing flow.py, categories.py, prefect.yaml, etc.
uv export --frozen --no-dev --no-editable -o requirements.txt
git add -A && git commit -m "update flow" && git push origin main
prefect deploy --name daily-ai-digest

# Trigger an ad-hoc run outside the schedule
prefect deployment run "daily-ai-digest/daily-ai-digest"
```

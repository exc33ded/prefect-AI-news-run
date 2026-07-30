# Prefect Cloud Setup

Step-by-step guide to setting up The AI Herald on Prefect Cloud. This is the "do it once" setup — after this, the pipeline runs automatically every day.

**Before you start:** Read [Prefect 101](../prefect-101.md) if you're new to Prefect. Read [API Keys & Secrets](05-api-keys-and-secrets.md) and have all your API keys ready.

---

## Prerequisites

- A [Prefect Cloud account](https://app.prefect.cloud) (free Hobby tier works)
- All API keys from [API Keys & Secrets](05-api-keys-and-secrets.md)
- Code pushed to GitHub
- `prefect` CLI installed (`uv sync` or `pip install prefect`)

---

## Step 1: Log In to Prefect Cloud

```bash
prefect cloud login
```

This opens a browser window to authenticate. After logging in, your CLI is connected to your Prefect Cloud workspace.

**Verify:**

```bash
prefect version
# Shows Prefect version + Cloud connection info
```

---

## Step 2: Create a Managed Work Pool

A work pool is the "kitchen" where your flow runs. We're using a **managed** work pool — Prefect provides the infrastructure.

```bash
prefect work-pool create ai-digest-managed-pool --type prefect:managed
```

**What this means:**
- Prefect provisions a container when the schedule fires
- The container runs the flow, then is destroyed
- You don't manage any servers or workers
- Free Hobby tier: 1 managed work pool is included

**Verify:**

```bash
prefect work-pool ls
```

Should show:

```
NAME                       TYPE             STATUS
ai-digest-managed-pool     prefect:managed  READY
```

---

## Step 3: Push Secrets to Prefect Cloud

Secrets are stored as Prefect Secret blocks. Run each command, replacing `YOUR_KEY` with actual values.

```bash
# 1. Tavily API key (required - AI news search)
python -c "from prefect.blocks.system import Secret; Secret(value='tvly-YOUR_KEY').save('tavily-api-key-1', overwrite=True)"

# 2. DeepSeek API key (required - LLM summarization)
python -c "from prefect.blocks.system import Secret; Secret(value='sk-YOUR_KEY').save('openai-api-key', overwrite=True)"

# 3. Groq API key (recommended - LLM fallback)
python -c "from prefect.blocks.system import Secret; Secret(value='gsk_YOUR_KEY').save('groq-api-key', overwrite=True)"

# 4. Resend API key (required - email delivery)
python -c "from prefect.blocks.system import Secret; Secret(value='re_YOUR_KEY').save('resend-api-key', overwrite=True)"

# 5. Email sender (defaults to onboarding@resend.dev if unset)
python -c "from prefect.blocks.system import Secret; Secret(value='onboarding@resend.dev').save('email-from', overwrite=True)"

# 6. Email recipient (required)
python -c "from prefect.blocks.system import Secret; Secret(value='you@example.com').save('email-to', overwrite=True)"

# 7. GitHub token (optional - web publishing)
python -c "from prefect.blocks.system import Secret; Secret(value='ghp_YOUR_TOKEN').save('github-token', overwrite=True)"

# 8. GitHub repo (optional - web publishing)
python -c "from prefect.blocks.system import Secret; Secret(value='exc33ded/prefect-AI-news-run').save('github-repo', overwrite=True)"
```

**Why `overwrite=True`?** You'll re-run these commands when updating keys. Without `overwrite=True`, Prefect throws an error if the block already exists.

**Verify:**

```bash
prefect block ls
```

Should show 8+ Secret blocks.

---

## Step 4: Export Requirements for Prefect Cloud

Prefect managed pools use pip, not uv. Export the lockfile to pip format:

```bash
uv export --frozen --no-dev --no-editable -o requirements.txt
```

**Verify the file was generated:**

```bash
head -20 requirements.txt
```

Should show pip-compatible format with hashes.

**Commit the requirements:**

```bash
git add requirements.txt
git commit -m "Export requirements for Prefect Cloud"
git push
```

---

## Step 5: Deploy

```bash
prefect deploy --name daily-ai-digest
```

**What happens:**
1. Prefect reads `prefect.yaml` — finds the deployment configuration
2. Registers the flow `daily_ai_digest/flow.py:daily_ai_digest`
3. Links it to the `ai-digest-managed-pool` work pool
4. Sets the cron schedule: `0 8 * * *` (daily at 8:00 AM) in `Asia/Calcutta`
5. Configures pull steps: `git_clone` → `pip_install_requirements`

**Verify:**

```bash
prefect deployment ls
```

Should show:

```
NAME                    FLOW              WORK POOL                 SCHEDULE
daily-ai-digest         daily_ai_digest   ai-digest-managed-pool    cron: 0 8 * * *
```

---

## Step 6: Trigger a Manual Test Run

Before trusting the schedule, verify everything works:

```bash
prefect deployment run "daily-ai-digest/daily-ai-digest"
```

**Monitor the run:**

```bash
prefect flow-run ls --limit 5
```

Or watch the Prefect Cloud UI:
1. Go to [app.prefect.cloud](https://app.prefect.cloud)
2. Your workspace → Flow Runs
3. Click the running flow → see live logs

**What to look for in the logs:**

```
Starting daily_ai_digest flow...
Searching: repos
Searching: skills
...
Search complete: 10/10 categories returned results
Processing results with LLM...
LLM processing complete
Rendering email...
Rendering web page...
Sending email... Done!
Publishing to GitHub Pages... Done!
Flow complete!
```

**Check the results:**
- Email: Check the recipient inbox (and spam folder)
- Web: Check `https://yourusername.github.io/your-repo/`

---

## Step 7: Enable GitHub Pages (Optional)

If you want the web edition publicly accessible:

1. Go to your GitHub repository → Settings → Pages
2. Source: Deploy from a branch
3. Branch: `main` → `/docs` folder
4. Save

The site will be available at `https://yourusername.github.io/your-repo/` within a few minutes.

**Note:** This is a one-time setup. Once enabled, the pipeline updates the site automatically on every run.

---

## Step 8: Let the Schedule Take Over

After a successful manual run, the schedule is active. The pipeline will run automatically every day at 8:00 AM IST.

**You can verify upcoming runs:**

```bash
prefect flow-run ls --limit 10
```

Or check the "Flow Runs" tab in the Prefect Cloud UI.

---

## What's Actually Happening on Schedule

When 8:00 AM IST arrives:

```
1. Prefect Cloud creates a flow run
2. Managed work pool provisions a container (prefecthq/prefect:3-latest image)
3. Pull Step 1: git clone https://github.com/your/repo.git (branch: main)
4. Pull Step 2: pip install -r requirements.txt
5. Flow execution: daily_ai_digest()
   ├─ 10 parallel Tavily searches
   ├─ DeepSeek summarization (fallback: Groq)
   ├─ Render email + web page
   ├─ Send email via Resend
   └─ Publish to GitHub Pages
6. Container is torn down
7. Logs available in Prefect Cloud UI
```

**Total runtime:** ~30-60 seconds.

---

## Updating the Deployment

When you change the code:

```bash
# 1. Push code to GitHub
git add .
git commit -m "Your changes"
git push

# 2. If dependencies changed, re-export requirements
uv export --frozen --no-dev --no-editable -o requirements.txt
git add requirements.txt
git commit -m "Update requirements"
git push

# 3. Re-deploy to update Prefect Cloud
prefect deploy --name daily-ai-digest
```

**Important:** Both the GitHub push AND the Prefect deploy are needed. The push makes code available to the container. The deploy tells Prefect Cloud about the updated deployment config.

---

## Troubleshooting Setup

### "ModuleNotFoundError: No module named 'prefect'"

You're running Prefect commands outside the virtual environment:

```bash
# Wrong
python -c "from prefect.blocks.system import Secret..."

# Right
uv run python -c "from prefect.blocks.system import Secret..."
```

### "Work pool 'ai-digest-managed-pool' not found"

The work pool wasn't created. Check:

```bash
prefect work-pool ls
```

If missing, create it:

```bash
prefect work-pool create ai-digest-managed-pool --type prefect:managed
```

### "Entrypoint 'daily_ai_digest/flow.py:daily_ai_digest' not found"

Prefect can't find the flow function. Make sure:
- The file path in `prefect.yaml` matches your repo structure
- The flow function is decorated with `@flow`
- The code is pushed to GitHub (Prefect clones it, so it must be committed)

### "Secret 'tavily-api-key-1' not found"

A required secret block is missing. Create it:

```bash
python -c "from prefect.blocks.system import Secret; Secret(value='your_key').save('tavily-api-key-1', overwrite=True)"
```

### Run stuck on "Late" or "Scheduled"

The managed work pool might be busy or unavailable. Check:
- Prefect Cloud status: [status.prefect.io](https://status.prefect.io)
- Your work pool is `READY`: `prefect work-pool ls`
- Hobby tier has limits — only 1 concurrent flow run

---

## Next Steps

- Understand the deployment → **[Deployment Guide](07-prefect-deployment-guide.md)**
- How the search works → **[Search Pipeline](08-search-pipeline.md)**
- All commands → **[Command Cheatsheet](16-command-cheatsheet.md)**
- Something broken? → **[Troubleshooting](17-troubleshooting.md)**

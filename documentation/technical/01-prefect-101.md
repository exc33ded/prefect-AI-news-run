# Prefect 101 — Fully Explained with This Project's Real Code

If you've never used Prefect before, this page explains everything by walking through exactly what this project does. Every concept is demonstrated with the actual code, config files, and commands from this repository. By the end, you'll understand Prefect AND how this project uses it.

---

## Quick Reality Check

Open `daily_ai_digest/flow.py`. You'll see this:

```python
from prefect import flow, task

@flow(log_prints=True)
def daily_ai_digest():
    ...  # ~80 lines of orchestration
```

That `@flow` decorator is the only thing making this a Prefect flow. The function itself is just Python. Prefect doesn't change how your code works — it adds instrumentation, scheduling, and retries on top.

---

## The prefect.yaml File — Explained Line by Line

This is the most important file. It defines everything Prefect Cloud needs to run your pipeline. Open `prefect.yaml` and follow along:

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/PrefectHQ/prefect/main/src/prefect/deployments/schemas/deployment.yaml

deployments:
  - name: daily-ai-digest
```

**What this is:** You're defining one deployment called `daily-ai-digest`. You can have multiple deployments (e.g., production + staging) in one file. Each has its own schedule, entrypoint, and work pool.

```yaml
    entrypoint: daily_ai_digest/flow.py:daily_ai_digest
```

**What this is:** This tells Prefect "the flow function is in the file `daily_ai_digest/flow.py` and the function is called `daily_ai_digest`." Prefect reads this file, finds the function with `@flow` on it, and registers it.

**How to verify it:** If you run `uv run prefect deploy --name daily-ai-digest` and it says "entrypoint not found," check that (a) the file path is correct, (b) the function has the `@flow` decorator, (c) you've pushed the code to GitHub.

```yaml
    parameters: {}
```

**What this is:** Arguments passed to your flow function. Empty here because `daily_ai_digest()` takes no parameters. If your flow had `def daily_ai_digest(date: str)`, you could set `parameters: {date: "2026-01-30"}`.

```yaml
    work_pool:
      name: ai-digest-managed-pool
      work_queue_name: default
      job_variables: {}
```

**What this is:** Where the flow runs. `name` is the work pool you create with `prefect work-pool create`. `type` (in the pool definition, not shown) is `prefect:managed` — meaning Prefect provisions the container. `work_queue_name: default` is the queue within the pool (you don't need to change this). `job_variables: {}` is where you'd add custom environment variables or container settings.

```yaml
    schedules:
      - cron: "0 8 * * *"
        timezone: "Asia/Calcutta"
        day_or: true
        active: true
```

**What this is:** The schedule. `cron: "0 8 * * *"` means "every day at 8:00 AM." The cron format is `minute hour day_of_month month day_of_week`. `timezone: "Asia/Calcutta"` is Indian Standard Time (UTC+5:30). `active: true` means the schedule is running. Set to `false` to pause.

```yaml
    pull:
      - prefect.deployments.steps.git_clone:
          repository: https://github.com/exc33ded/prefect-AI-news-run.git
          branch: main
          access_token: null

      - prefect.deployments.steps.pip_install_requirements:
          directory: "{{ git_clone.directory }}"
          requirements_file: requirements.txt
          pip_version: ""
```

**What this is:** The two steps that run BEFORE your flow, to set up the environment.

**Step 1 — `git_clone`:** Clones the repo from GitHub at the `main` branch. `access_token: null` because it's a public repo. For private repos, you'd put a token here.

**Step 2 — `pip_install_requirements`:** Installs all dependencies from `requirements.txt`. The `directory` uses `{{ git_clone.directory }}` — a variable auto-populated by step 1 that points to the cloned repo. `pip_version: ""` means "use whatever pip comes with the container image."

```yaml
    enforce_parameter_schema: true
```

**What this is:** Validates that any parameters you pass match the flow function's signature. Keeps things from silently breaking when parameters don't match.

---

## API Keys & Secrets — The Full Setup

This project needs 5 external services. Here's every key, where to get it, and how to configure it for both local and Prefect Cloud.

### The Secret Loading System

All secrets go through `daily_ai_digest/config.py`:

```python
from prefect.blocks.system import Secret

def get_secret(name: str) -> Optional[str]:
    # Step 1: Try .env file (local development)
    value = os.getenv(name)
    if value:
        return value

    # Step 2: Try Prefect Secret block (Prefect Cloud)
    try:
        block_name = name.lower().replace("_", "-")
        return Secret.load(block_name).get()
    except Exception:
        return None
```

Same code works in both environments. No `if LOCAL` branches anywhere.

### Complete Secret Table

| Secret | Service | How to Get | Local (.env) | Prefect Cloud Block |
|--------|---------|-----------|-------------|-------------------|
| `TAVILY_API_KEY_1` | Tavily Search | [tavily.com](https://tavily.com) → sign up → API Keys | `TAVILY_API_KEY_1=tvly-xxx` | `tavily-api-key-1` |
| `TAVILY_API_KEY_2..10` | Tavily (fallback) | Create extra Tavily accounts | `TAVILY_API_KEY_2=tvly-yyy` | `tavily-api-key-2` |
| `OPENAI_API_KEY` | DeepSeek AI | [platform.deepseek.com](https://platform.deepseek.com) → API Keys | `OPENAI_API_KEY=sk-xxx` | `openai-api-key` |
| `GROQ_API_KEY` | Groq AI (fallback) | [console.groq.com](https://console.groq.com) → API Keys | `GROQ_API_KEY=gsk_xxx` | `groq-api-key` |
| `RESEND_API_KEY` | Resend Email | [resend.com](https://resend.com) → API Keys | `RESEND_API_KEY=re_xxx` | `resend-api-key` |
| `EMAIL_FROM` | Sender address | Defaults to `onboarding@resend.dev` | `EMAIL_FROM=onboarding@resend.dev` | `email-from` |
| `EMAIL_TO` | Recipient | Your email address | `EMAIL_TO=you@example.com` | `email-to` |
| `GITHUB_TOKEN` | GitHub (publishing) | Settings → Developer settings → PAT → `repo` scope | `GITHUB_TOKEN=ghp_xxx` | `github-token` |
| `GITHUB_REPO` | Target repo | Format: `owner/repo` | `GITHUB_REPO=exc33ded/repo` | `github-repo` |

### Setting Up Secrets

**Local (.env):**

```bash
cp .env.example .env
# Edit .env with your actual keys
```

**Prefect Cloud (Secret blocks):**

```bash
python -c "from prefect.blocks.system import Secret; Secret(value='tvly-xxx').save('tavily-api-key-1', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='sk-xxx').save('openai-api-key', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='gsk_xxx').save('groq-api-key', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='re_xxx').save('resend-api-key', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='onboarding@resend.dev').save('email-from', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='you@example.com').save('email-to', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='ghp_xxx').save('github-token', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='owner/repo').save('github-repo', overwrite=True)"
```

**The naming trick:** `.env` uses `UPPERCASE_UNDERSCORES`. Prefect blocks use `lowercase-hyphens`. `get_secret()` converts automatically: `TAVILY_API_KEY_1` → `tavily-api-key-1`. You never need to think about it.

---

## The Flow Code — Explained

Here's the actual flow function from `daily_ai_digest/flow.py`, annotated:

```python
@flow(log_prints=True)
def daily_ai_digest():
    # ═══ STAGE 1: SEARCH ═══
    # Launch 10 parallel Tavily searches
    futures = submit_all_searches()

    # Collect results — each category individually error-wrapped
    raw_by_category = {}
    for key, future in futures.items():
        try:
            raw_by_category[key] = future.result()
        except Exception as e:
            print(f"Search failed for {key}: {e}")
            raw_by_category[key] = []  # Empty = category skipped

    # ═══ STAGE 2: LLM PROCESSING ═══
    # DeepSeek → Groq → empty (automatic fallback)
    digest = process_results(raw_by_category)

    # Build the edition URL for links
    date_str = datetime.now().strftime("%Y-%m-%d")
    edition_url = f"https://{owner}.github.io/{repo}/{date_str}.html"

    # ═══ STAGE 3: EMAIL ═══
    try:
        email_html = render_email(digest, edition_url)
        send_email(email_html, date_str)
    except Exception as e:
        print(f"Email stage failed (continuing): {e}")

    # ═══ STAGE 4: WEB PUBLISHING ═══
    try:
        editions = fetch_archive_editions()
        page_html, meta = render_page(digest, editions)
        publish_page(page_html, editions, meta)
    except Exception as e:
        print(f"Publishing stage failed (continuing): {e}")
```

**Key pattern — stage isolation:** Email and publishing are in separate try/except blocks. If email fails, publishing still happens. If publishing fails, email still sends. No single stage crash kills the whole pipeline.

---

## The Task Code — Explained

Here's how individual tasks work, with the real search task:

```python
# In search.py
@task
def search_category(key: str, label: str, query: str) -> list[dict]:
    """Search one category. Returns [] on failure."""
    keys = _tavily_keys()                    # Get available API keys
    results = _search_with_fallback(query, keys)  # Try keys sequentially
    return _normalize(results, key)
```

And here's a task with retry logic (from `process.py`):

```python
@task(retries=2, retry_delay_seconds=[5, 15])
def process_results(raw_by_category: dict) -> dict:
    """Summarize with DeepSeek. Fall back to Groq. Return empty if both fail."""
    ...
```

**The retry timeline:**
- Attempt 1: DeepSeek → fails
- Wait 5 seconds
- Attempt 2 (retry 1): Groq → fails
- Wait 15 seconds
- Attempt 3 (retry 2): Empty digest returned
- Total: ~20 seconds if both providers are down

And here's how parallel execution works:

```python
# In search.py
def submit_all_searches():
    futures = {}
    for cat in CATEGORIES:
        # .submit() returns immediately — tasks run in background
        future = search_category.submit(cat["key"], cat["label"], cat["query"])
        futures[cat["key"]] = future
    return futures
    # 10 searches running at the same time → ~3 seconds total, not 30
```

---

## The Full Lifecycle — What Actually Happens

### When You Run Locally

```bash
uv run python main.py
```

```
1. Python starts the flow (no Prefect Cloud involved)
2. .env is loaded by python-dotenv
3. Every get_secret() call reads from .env
4. @flow and @task decorators add logging/instrumentation
5. 10 .submit() calls → 10 parallel background tasks
6. Tasks execute in parallel, results collected
7. Email sent, page rendered, published
8. Terminal output shows everything
```

### When the Schedule Fires on Prefect Cloud

```
[SCHEDULE: 8:00 AM IST — 2026-01-30]
         │
         ▼
┌──────────────────────────────────────────┐
│ Prefect Cloud creates a flow run          │
│ - Assigns a run ID                        │
│ - Links to the daily-ai-digest deployment │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│ Managed work pool provisions container     │
│ - Image: prefecthq/prefect:3-latest       │
│ - Has Python + pip + git                  │
│ - 2 CPU, 4 GB RAM (Hobby tier)            │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│ Pull Step 1: git_clone                     │
│ - git clone https://github.com/...         │
│ - Branch: main                             │
│ - Directory: /tmp/prefect-flow-xxx/        │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│ Pull Step 2: pip_install_requirements      │
│ - cd /tmp/prefect-flow-xxx/               │
│ - pip install -r requirements.txt          │
│ - ~50 packages installed from lockfile     │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│ Flow execution starts                      │
│                                            │
│ import daily_ai_digest.flow                │
│ daily_ai_digest()                          │
│                                            │
│ 1. submit_all_searches()                   │
│    └─ 10 × search_category.submit()        │
│       └─ Each: TavilyClient.search()       │
│       └─ Keys: try 1→2→3... on failure    │
│    └─ Wait for all futures                 │
│                                            │
│ 2. process_results(raw_by_category)        │
│    └─ _index_raw() → assign IDs            │
│    └─ DeepSeek: summarize by ID            │
│    └─ If fail → Groq: summarize by ID      │
│    └─ If fail → _empty_digest()            │
│    └─ _resolve_picks() → rehydrate data    │
│                                            │
│ 3. render_email(digest, edition_url)       │
│    └─ Jinja2: templates/email.html         │
│    └─ Top 2 per category                   │
│                                            │
│ 4. render_page(digest, editions)           │
│    └─ Jinja2: templates/edition.html       │
│    └─ Lead story + sections + vol/issue    │
│                                            │
│ 5. send_email(email_html, date_str)        │
│    └─ Resend API: POST /emails             │
│    └─ Retry 2× on failure (5s, 15s)        │
│                                            │
│ 6. publish_page(page_html, editions, meta) │
│    └─ GitHub Contents API:                 │
│       ├─ PUT docs/index.html               │
│       ├─ PUT docs/{date}.html              │
│       ├─ PUT docs/archive.json             │
│       └─ PUT docs/archive.html             │
│                                            │
│ Each step 3-6 individually try/except      │
│ wrapped — one failure doesn't cascade      │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│ Flow completes                             │
│ - Logs saved to Prefect Cloud UI           │
│ - Flow run marked "Completed" or "Failed"  │
│ - Container destroyed                      │
│                                            │
│ ~30-60 seconds total                       │
└──────────────────────────────────────────┘
         │
         ▼
   ┌──────────┐     ┌─────────────┐
   │  INBOX   │     │  WEBSITE    │
   │  Email   │     │  Updated    │
   └──────────┘     └─────────────┘
```

---

## The Deploy Command — What It Actually Does

```bash
prefect deploy --name daily-ai-digest
```

1. Reads `prefect.yaml` — finds the `daily-ai-digest` deployment
2. Reads the entrypoint file — validates `daily_ai_digest/flow.py:daily_ai_digest` exists and has `@flow`
3. Registers in Prefect Cloud:
   - Flow metadata
   - Schedule (cron + timezone)
   - Work pool + queue assignment
   - Pull steps
4. Returns a deployment ID

**After deploying, the schedule is live.** You don't start anything. Prefect Cloud handles everything.

**Common gotcha:** `prefect deploy` doesn't push code to GitHub. You must `git push` separately. The deploy command just tells Prefect Cloud about the configuration.

---

## Prefect vs. What You Know

### Prefect vs. Cron

| Cron | Prefect |
|------|---------|
| Runs on your server | Runs on Prefect's infrastructure |
| No retry logic | Built-in retries with configurable delays |
| Logs to syslog/files | Logs in web dashboard |
| Secrets in env files/scripts | Secrets encrypted in Prefect Cloud |
| You manage the server | Prefect manages containers |
| Schedule only (cron string) | Schedule + manual triggers + params |

### Prefect vs. GitHub Actions

| GitHub Actions | Prefect |
|---------------|---------|
| Runs on GitHub's CI infra | Runs on Prefect's infra |
| Triggered by git events | Triggered by schedule |
| Time limit (6 hrs free) | No limit (this project: 60s) |
| Good for CI/CD | Good for scheduled jobs |

---

## Setting Up Prefect Cloud — The Full Sequence

When you're ready to deploy, here's every command, in order:

```bash
# 1. Create a Prefect Cloud account
#    Go to https://app.prefect.cloud → sign up (free Hobby tier)

# 2. Log the CLI into your account
prefect cloud login
#    Opens browser → authenticate → CLI is connected

# 3. Create a managed work pool (serverless!)
prefect work-pool create ai-digest-managed-pool --type prefect:managed

# 4. Push all secrets to Prefect Cloud
python -c "from prefect.blocks.system import Secret; Secret(value='tvly-xxx').save('tavily-api-key-1', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='sk-xxx').save('openai-api-key', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='gsk_xxx').save('groq-api-key', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='re_xxx').save('resend-api-key', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='onboarding@resend.dev').save('email-from', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='you@example.com').save('email-to', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='ghp_xxx').save('github-token', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='owner/repo').save('github-repo', overwrite=True)"

# 5. Export pip-compatible requirements
uv export --frozen --no-dev --no-editable -o requirements.txt
git add requirements.txt && git commit -m "Export requirements" && git push

# 6. Register the deployment
prefect deploy --name daily-ai-digest

# 7. Trigger a manual test run
prefect deployment run "daily-ai-digest/daily-ai-digest"

# 8. Check the run in the Prefect Cloud UI
#    https://app.prefect.cloud → Flow Runs → click your run → see live logs
```

**Verify everything worked:**

```bash
prefect deployment ls     # Shows your deployment
prefect work-pool ls      # Shows your pool (READY)
prefect block ls | grep secret  # Shows all secret blocks
prefect flow-run ls --limit 5   # Shows recent runs
```

---

## The uv → pip Bridge (Why This Project Has Two Package Managers)

```
pyproject.toml     ←  You declare dependencies here
      │
      ▼
  uv lock          ←  Resolves exact versions (creates uv.lock)
      │
      ▼
  uv.lock          ←  Canonical lockfile (commit this to git)
      │
      ▼
  uv export        ←  Converts uv format → pip format
      │
      ▼
requirements.txt   ←  Prefect Cloud reads this
```

**Why?** You use `uv` locally because it's fast. Prefect Cloud uses `pip` because managed containers have pip but not uv. The `requirements.txt` file is the bridge. Re-export it whenever dependencies change:

```bash
uv export --frozen --no-dev --no-editable -o requirements.txt
```

---

## What Prefect Concepts This Project Uses

| Concept | File | What It Does |
|---------|------|-------------|
| `@flow(log_prints=True)` | `flow.py` | Orchestrator — tracks the whole run |
| `@task` | `search.py` | Unit of work — runs independently |
| `@task(retries=2)` | `process.py`, `notify.py` | Auto-retry on failure |
| `@task(retry_delay_seconds=[5, 15])` | `process.py`, `notify.py` | Backoff between retries |
| `.submit()` | `search.py` | Parallel execution (10 at once) |
| `Secret.load()` | `config.py` | Fetch API keys securely |
| `prefect.yaml` | Root | Deployment config (schedule, work pool, pull steps) |
| `prefect deploy` | CLI | Register deployment in Prefect Cloud |
| Managed work pool | `prefect.yaml` | Serverless — no worker to manage |

---

## Next Steps

- Ready to set up Prefect Cloud for real? → **[06-prefect-cloud-setup.md](backend/06-prefect-cloud-setup.md)**
- Deep dive into `prefect.yaml` → **[07-prefect-deployment-guide.md](backend/07-prefect-deployment-guide.md)**
- Understand the code architecture → **[02-architecture-overview.md](backend/02-architecture-overview.md)**
- All the API keys explained → **[05-api-keys-and-secrets.md](backend/05-api-keys-and-secrets.md)**
- Just want to run locally? → **[02-getting-started-local.md](../non-technical/02-getting-started-local.md)**

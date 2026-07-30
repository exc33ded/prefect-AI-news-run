# Configuration Reference

Every configurable value in the project, where it lives, what it controls, and what happens if you change it.

---

## Search Configuration

### Categories (`daily_ai_digest/categories.py`)

```python
CATEGORIES = [
    {
        "key": "repos",
        "label": "🛠️ Repos",
        "query": "new AI tools released today 2026 GitHub repository"
    },
    # ... 9 more categories
]
```

| Field | Type | Purpose | Where Used |
|-------|------|---------|------------|
| `key` | str | Internal identifier | Used throughout the codebase to reference this category |
| `label` | str | Display name (shown in email, website, sidebar) | Templates, email rendering |
| `query` | str | Search query sent to Tavily | `search.py:_search_with_fallback()` |

### Stale Repo Threshold (`daily_ai_digest/search.py`)

```python
STALE_REPO_DAYS = 90
```

| Value | Effect |
|-------|--------|
| `90` | GitHub repos older than 90 days are filtered out from the `repos` category |
| `0` | All GitHub repos filtered (only non-GitHub results shown) |
| `None` or very large | Effectively no filtering |

### Search Parameters (`daily_ai_digest/search.py`)

```python
response = client.search(
    query=query,
    search_depth="advanced",   # "basic" or "advanced"
    max_results=10             # Number of results per category
)
```

| Parameter | Default | Effect |
|-----------|---------|--------|
| `search_depth` | `"advanced"` | `"basic"` is faster but less thorough; `"advanced"` is slower but finds more relevant results |
| `max_results` | `10` | More results = more LLM prompt tokens = higher cost but better coverage |

### Tavily Key Count (`daily_ai_digest/search.py`)

```python
for i in range(1, 11):  # Checks TAVILY_API_KEY_1 through TAVILY_API_KEY_10
```

Change the `11` to support more or fewer keys.

---

## LLM Configuration

### Provider Selection (`daily_ai_digest/process.py`)

```python
# DeepSeek (primary)
OpenAI(
    api_key=get_secret("OPENAI_API_KEY"),
    base_url="https://api.deepseek.com",
)
model = "deepseek-v4-flash"

# Groq (fallback)
OpenAI(
    api_key=get_secret("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)
model = "llama-3.3-70b-versatile"
```

### LLM Parameters (`daily_ai_digest/process.py`)

```python
response = client.chat.completions.create(
    model=model,
    messages=[...],
    temperature=0.3,
    max_tokens=4096,
)
```

| Parameter | Default | Effect |
|-----------|---------|--------|
| `temperature` | `0.3` | Lower = more deterministic/factual; higher = more creative/varied. Range: 0.0-2.0 |
| `max_tokens` | `4096` | Maximum output tokens. Increase for longer summaries or more items |

### Summary Length (`daily_ai_digest/process.py`)

Controlled by the system prompt:

```
"write a 3-5 sentence summary"
```

Change to "1-2 sentence summary" for a more concise digest or "detailed paragraph" for longer summaries.

### Items Per Category (`daily_ai_digest/process.py`)

```
"select the 3-5 most significant items"
```

Change to "1-2 most significant" for fewer stories per category or increase for more coverage (at the cost of higher token usage).

### Retry Configuration (`daily_ai_digest/process.py`)

```python
@task(retries=2, retry_delay_seconds=[5, 15])
```

| Parameter | Default | Effect |
|-----------|---------|--------|
| `retries` | `2` | Number of retry attempts after initial failure |
| `retry_delay_seconds` | `[5, 15]` | Wait 5s before first retry, 15s before second retry |

---

## Email Configuration

### Sender/Recipient (`daily_ai_digest/notify.py`)

```python
"from": get_secret("EMAIL_FROM") or "onboarding@resend.dev",
"to": [get_secret("EMAIL_TO")],
"subject": f"THE AI DAILY — {date_str}",
```

| Setting | Source | Default |
|---------|--------|---------|
| From address | `EMAIL_FROM` secret | `onboarding@resend.dev` |
| To address | `EMAIL_TO` secret | (required, no default) |
| Subject | Hardcoded format | `THE AI DAILY — YYYY-MM-DD` |

### Email Retry (`daily_ai_digest/notify.py`)

```python
@task(retries=2, retry_delay_seconds=[5, 15])
```

Same retry pattern as LLM processing — 2 retries with 5s and 15s delays.

### Items Per Category in Email (`daily_ai_digest/format_email.py`)

```python
top_two[key] = items[:2]  # Top 2 per category in email
```

Change to `items[:3]` for more stories in email (but may cause Gmail clipping at 102KB).

---

## Publishing Configuration

### Repository (`daily_ai_digest/publish_github.py`)

```python
repo = get_secret("GITHUB_REPO")  # Format: "owner/repo"
```

### File Paths (`daily_ai_digest/publish_github.py`)

```python
_put_file(client, "docs/index.html", page_html)          # Latest edition
_put_file(client, f"docs/{date_str}.html", page_html)    # Archive edition
_put_file(client, "docs/archive.json", archive_json)      # Metadata
_put_file(client, "docs/archive.html", archive_html)      # Calendar page
```

Change `docs/` to a different directory if using a different GitHub Pages source folder.

### Edition URL Format (`daily_ai_digest/flow.py`)

```python
edition_url = f"https://{owner}.github.io/{repo}/{date_str}.html"
```

Update if using a custom domain.

---

## Schedule Configuration

### Cron Schedule (`prefect.yaml`)

```yaml
schedules:
  - cron: "0 8 * * *"
    timezone: "Asia/Calcutta"
```

| Field | Value | Meaning |
|-------|-------|---------|
| `cron` | `"0 8 * * *"` | Every day at 8:00 AM |
| `timezone` | `"Asia/Calcutta"` | Indian Standard Time (UTC+5:30) |

### Manual Override

The schedule can be paused from Prefect Cloud UI without editing `prefect.yaml`:
- Deployments → daily-ai-digest → Schedule → Toggle off

---

## Deployment Configuration

### Work Pool (`prefect.yaml`)

```yaml
work_pool:
  name: ai-digest-managed-pool
  work_queue_name: default
  job_variables: {}
```

| Field | Value | Notes |
|-------|-------|-------|
| `name` | `ai-digest-managed-pool` | Must exist in Prefect Cloud |
| `type` | `prefect:managed` | Serverless — no self-hosted worker |
| `work_queue_name` | `default` | Default queue within the pool |

### Pull Steps (`prefect.yaml`)

```yaml
pull:
  - prefect.deployments.steps.git_clone:
      repository: https://github.com/user/repo.git
      branch: main
      access_token: null

  - prefect.deployments.steps.pip_install_requirements:
      directory: "{{ git_clone.directory }}"
      requirements_file: requirements.txt
```

---

## Python Dependencies (`pyproject.toml`)

```toml
dependencies = [
    "httpx>=0.28.1",
    "jinja2>=3.1.6",
    "openai>=2.49.0",
    "prefect>=3.8.0",
    "python-dotenv>=1.2.2",
    "resend>=2.35.0",
    "tavily-python>=0.7.26",
]
```

| Dependency | Purpose |
|-----------|---------|
| `httpx` | HTTP client for GitHub API calls |
| `jinja2` | HTML template rendering |
| `openai` | LLM API client (used with DeepSeek and Groq) |
| `prefect` | Flow orchestration |
| `python-dotenv` | Local `.env` file loading |
| `resend` | Email delivery |
| `tavily-python` | AI news search API client |

---

## Feature Flags (Implicit)

There are no explicit feature flags, but behavior can be controlled by the presence of secrets:

| Secret | If Missing |
|--------|-----------|
| `TAVILY_API_KEY_1` | Search phase fails → empty digest |
| `OPENAI_API_KEY` | DeepSeek unavailable → falls back to Groq |
| `GROQ_API_KEY` | No Groq fallback → empty digest if DeepSeek also fails |
| `RESEND_API_KEY` | Email skipped |
| `EMAIL_TO` | Email skipped |
| `GITHUB_TOKEN` | Publishing skipped |
| `GITHUB_REPO` | Publishing skipped |

---

## Environment Detection

The code auto-detects its environment:

```python
# In config.py
def get_secret(name):
    # Try .env first (local dev)
    value = os.getenv(name)
    if value:
        return value

    # Try Prefect blocks (Prefect Cloud)
    try:
        return Secret.load(...).get()
    except:
        return None
```

**Effect:** No `if LOCAL` or `if CLOUD` branching anywhere in the codebase. The same function handles both environments transparently.

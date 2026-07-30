# Project Structure

A file-by-file walkthrough of the entire repository. Every file, what it does, and why it exists.

---

## Repository Layout

```
prefect-AI-news-run/
│
├── .claude/                         ← Claude Code integration
├── .commandcode/                    ← CommandCode configuration
├── .omp/                            ← OMP integration
│
├── daily_ai_digest/                 ← ★ CORE PACKAGE ★
│   ├── __init__.py
│   ├── flow.py                      ← Main orchestrator
│   ├── categories.py                ← Search category definitions
│   ├── config.py                    ← Secret loading
│   ├── search.py                    ← Tavily search
│   ├── process.py                   ← LLM summarization
│   ├── format_email.py              ← Email rendering
│   ├── format_page.py               ← Web page rendering
│   ├── notify.py                    ← Email delivery
│   ├── publish_github.py            ← GitHub Pages publishing
│   └── templates/                   ← Jinja2 HTML templates
│       ├── email.html               ← Vintage-editorial email
│       ├── edition.html             ← Gothic newspaper page
│       └── archive.html             ← Calendar-grid archive
│
├── docs/                            ← Published output (GitHub Pages)
│   ├── index.html                   ← Latest edition (auto-generated)
│   ├── {YYYY-MM-DD}.html            ← Archived editions (auto-generated)
│   ├── archive.html                 ← Browseable archive (auto-generated)
│   ├── archive.json                 ← Schema metadata (auto-generated)
│   └── mockups/                     ← Design exploration
│
├── documentation/                   ← ★ PROJECT DOCUMENTATION ★
│   ├── non-technical/               ← For users/readers
│   └── technical/                   ← For developers
│       ├── backend/
│       └── frontend/
│
├── openspec/                        ← Spec-driven development
│   ├── config.yaml
│   └── changes/
│
├── scratchpad/                      ← Dev scratch files (gitignored)
│
├── .env                             ← Local secrets (gitignored)
├── .env.example                     ← Template for local secrets
├── .gitignore                       ← Git ignore rules
├── .python-version                  ← Python 3.11
├── CLAUDE.md                        ← Claude Code guidance
├── main.py                          ← Local entrypoint
├── prefect.yaml                     ← Prefect Cloud deployment config
├── pyproject.toml                   ← UV project definition
├── README.md                        ← Project README
├── requirements.txt                 ← Pip-locked deps (for Prefect Cloud)
├── test_flow.py                     ← Self-test suite
└── uv.lock                          ← UV lockfile
```

---

## Core Package (`daily_ai_digest/`)

### `__init__.py`

Empty. Makes `daily_ai_digest` a Python package so imports work:

```python
from daily_ai_digest.flow import daily_ai_digest
```

### `flow.py` — The Orchestrator

The main `@flow` function that coordinates the entire pipeline. This is the entrypoint for both local execution and Prefect Cloud.

```python
@flow(log_prints=True)
def daily_ai_digest():
    ...
```

**What it does (in order):**

1. Calls `submit_all_searches()` — launches 10 parallel Tavily search tasks via `.submit()`
2. Collects results into `raw_by_category` dict, with per-category try/except (one failure doesn't kill the whole collection)
3. Calls `process_results(raw_by_category)` — sends to DeepSeek/Groq for summarization
4. Calls `render_email(digest, edition_url)` — renders the email template
5. Calls `fetch_archive_editions()` — reads past editions from GitHub
6. Calls `render_page(digest, editions)` — renders the web edition template
7. Calls `send_email(email_html, date_str)` — delivers via Resend
8. Calls `publish_page(page_html, editions, meta)` — publishes to GitHub Pages

**Key design:** Steps 4-8 are individually try/except wrapped. An email failure doesn't prevent publishing, and vice versa.

### `categories.py` — Search Category Definitions

Defines the 10 categories that are searched each day.

```python
CATEGORIES = [
    {
        "key": "repos",
        "label": "🛠️ Repos",
        "query": "new AI tools released today 2026 GitHub repository"
    },
    {
        "key": "skills",
        "label": "🧠 Skills",
        "query": "new AI agent skills extensions plugins 2026"
    },
    # ... 8 more categories
]
```

**Why a data structure, not hardcoded:** Adding a category is a one-line addition. The search, processing, rendering, and email stages all iterate over `CATEGORIES`, so a new category propagates automatically.

### `config.py` — Secret Loading

Unified secret access for both local development and Prefect Cloud.

```python
def get_secret(name: str) -> Optional[str]:
    # Try environment variable first
    value = os.getenv(name)
    if value:
        return value

    # Try Prefect Secret block
    try:
        block_name = name.lower().replace("_", "-")
        return Secret.load(block_name).get()
    except Exception:
        return None
```

**The naming convention:** `.env` uses `TAVILY_API_KEY_1` (uppercase, underscores). Prefect blocks use `tavily-api-key-1` (lowercase, hyphens). `get_secret()` handles the conversion automatically.

### `search.py` — Tavily Search Pipeline

Searches 10 categories using the Tavily API, with multiple key rotation and freshness filtering.

**Key functions:**

- `search_category(key, label, query)` — `@task` that searches one category
- `_tavily_keys()` — reads up to 10 `TAVILY_API_KEY_N` secrets
- `_search_with_fallback(query, keys)` — tries keys sequentially on failure
- `_normalize(results)` — maps raw Tavily output to `{title, url, snippet, published_date}`
- `_github_repo_age_days(url)` — queries GitHub API for repo creation date
- `_filter_stale_repos(results)` — removes repos older than 90 days (only for `repos` category)
- `submit_all_searches()` — fires one `.submit()` per category for parallel execution

**Key design:** Parallel submission via `.submit()` means 10 searches run concurrently, not sequentially. Total search time = slowest individual search, not sum of all 10.

### `process.py` — LLM Summarization

Sends search results to the AI for summarization and ranking.

**Key functions:**

- `process_results(raw_by_category)` — `@task(retries=2)` main processing task
- `_build_openai_client()` — creates OpenAI-compatible client pointing to DeepSeek
- `_index_raw(raw_results)` — assigns positional IDs to raw items
- `_build_system_prompt()` — instructs the LLM to select by ID, write summaries only
- `_resolve_picks(picks, indexed_raw)` — resolves LLM's ID references back to real data
- `_empty_digest(categories)` — returns empty results if both LLM providers fail

**Key design:** The LLM prompt explicitly says "return JSON with `{id, summary}` only. NEVER write titles or URLs." This is the anti-hallucination mechanism — the LLM only touches summaries.

### `format_email.py` — Email HTML Rendering

Renders the email from a Jinja2 template.

```python
@task
def render_email(digest, edition_url):
    env = Environment(loader=PackageLoader("daily_ai_digest", "templates"))
    template = env.get_template("email.html")
    return template.render(
        date=date_str,
        edition_url=edition_url,
        categories=categories,  # top 2 items per category
        category_labels=labels,  # category display names
        ...
    )
```

**Key design:** The template receives pre-processed "top 2 per category" data. The rendering task doesn't filter — that's the flow's job.

### `format_page.py` — Web Edition Rendering

Renders the daily edition page from a Jinja2 template.

```python
@task
def render_page(digest, editions):
    # Extract lead story
    lead = _extract_lead(digest)

    # Build category sections
    sections = _build_sections(digest)

    # Calculate Volume and Issue numbers
    vol, no = _volume_and_issue(editions)

    env = Environment(loader=PackageLoader("daily_ai_digest", "templates"))
    template = env.get_template("edition.html")
    html = template.render(...)
    return html, {"date": date_str, "vol": vol, "no": no, ...}
```

**Key designs:**
- Lead story is the first item from the first non-empty category
- Volume uses Roman numerals, calculated from months since the first edition
- Issue resets to 1 each month
- Results include `meta` alongside HTML — used by the publishing step

### `notify.py` — Email Delivery

Sends the rendered email via Resend API.

```python
@task(retries=2, retry_delay_seconds=[5, 15])
def send_email(email_html, date_str):
    resend.api_key = get_secret("RESEND_API_KEY")
    params = {
        "from": get_secret("EMAIL_FROM") or "onboarding@resend.dev",
        "to": [get_secret("EMAIL_TO")],
        "subject": f"THE AI DAILY — {date_str}",
        "html": email_html,
    }
    resend.Emails.send(params)
```

**Key design:** Uses `@task(retries=2)` — if Resend is transiently down, the task retries twice with 5-second and 15-second delays.

### `publish_github.py` — GitHub Pages Publishing

Publishes the rendered HTML to GitHub Pages and maintains the archive.

**Key functions:**

- `fetch_archive_editions()` — `@task` that reads `docs/archive.json` from GitHub
- `publish_page(html, editions, meta)` — `@task` that writes all output files
- `_put_file(client, path, content)` — PUTs a file via GitHub Contents API
- `_update_archive(client, editions, meta)` — appends new edition, regenerates archive page

**API interaction pattern:**

```python
# Every PUT requires the current SHA (for conflict detection)
get_resp = await client.get(f"https://api.github.com/repos/{repo}/contents/{path}")
sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None

content_b64 = base64.b64encode(content.encode()).decode()
put_resp = await client.put(
    f"https://api.github.com/repos/{repo}/contents/{path}",
    json={"message": "Update edition", "content": content_b64, "sha": sha},
)
```

**Key design:** The SHA-based update-or-create pattern ensures idempotency. If the file exists, its SHA must be provided. If it doesn't exist, SHA is omitted. This follows GitHub's Contents API requirements.

---

## Templates (`daily_ai_digest/templates/`)

### `email.html`

Vintage-editorial HTML email. Uses inline CSS only (no stylesheets, no `@import`, no external fonts in default config) for maximum email client compatibility.

**Structure:** Masthead → AI disclaimer → Category sections (top 2 per category) → CTA button → Footer

### `edition.html`

Gothic/parchment newspaper website (~425 lines). Full CSS with animations, dark/light theme, 3-column layout.

**Structure:** Masthead → Dateline → Theme toggle → Lead story (drop-cap) → Index rail (sidebar) → Category sections (3-column) → Papers side-box → Footer with archive link

### `archive.html`

Interactive calendar archive page (~320 lines). Displays all past editions in a grid, with month/year selectors and popout modals.

**Structure:** Header → Month/Year selector → Calendar grid → Popout modal (edition details)

---

## Root-Level Files

### `main.py`

Local entrypoint. The simplest possible file:

```python
from daily_ai_digest.flow import daily_ai_digest

if __name__ == "__main__":
    daily_ai_digest()
```

Run with `uv run python main.py` for local execution.

### `prefect.yaml`

Prefect Cloud deployment configuration.

**Key sections:**
- `deployments[0].name` — `"daily-ai-digest"`
- `deployments[0].entrypoint` — `"daily_ai_digest/flow.py:daily_ai_digest"`
- `deployments[0].work_pool.name` — `"ai-digest-managed-pool"`
- `deployments[0].work_pool.type` — `"prefect:managed"`
- `deployments[0].schedules[0].cron` — `"0 8 * * *"`
- `deployments[0].schedules[0].timezone` — `"Asia/Calcutta"`
- `deployments[0].pull[0]` — `git_clone`
- `deployments[0].pull[1]` — `pip_install_requirements`

### `pyproject.toml`

UV project definition. Key sections:

```toml
[project]
name = "daily-ai-digest"
requires-python = ">=3.11"
dependencies = [
    "httpx>=0.28.1",        # GitHub API calls
    "jinja2>=3.1.6",        # HTML templating
    "openai>=2.49.0",       # DeepSeek & Groq (OpenAI-compatible)
    "prefect>=3.8.0",       # Workflow orchestration
    "python-dotenv>=1.2.2", # Local .env loading
    "resend>=2.35.0",       # Email delivery
    "tavily-python>=0.7.26",# AI news search
]
```

### `requirements.txt`

Pip-compatible lockfile (~119 KB). Exported from `uv.lock`:

```bash
uv export --frozen --no-dev --no-editable -o requirements.txt
```

This file is read by Prefect Cloud's `pip_install_requirements` pull step. It must be re-exported after any dependency changes.

### `test_flow.py`

Self-test suite (15 test functions). Tests parsing, fallback behavior, anti-hallucination, search normalization, repo age computation, and filtering.

Run with:

```bash
uv run python test_flow.py
```

### `.env` / `.env.example`

Local secrets (`.env` is gitignored; `.env.example` is committed as a template). See [API Keys & Secrets](05-api-keys-and-secrets.md) for the complete reference.

### `CLAUDE.md`

Guidance for Claude Code — architecture summary, commands, secrets pattern, and the dual-dependency (uv + pip) workflow.

---

## Published Output (`docs/`)

The `docs/` directory is both the GitHub Pages root and the output destination for the pipeline. Files are written here via GitHub Contents API by `publish_github.py`.

| File | Writer | Purpose |
|------|--------|---------|
| `index.html` | `publish_page()` | Latest edition (overwritten each run) |
| `{date}.html` | `publish_page()` | Permanent archive of each edition |
| `archive.html` | `_update_archive()` | Browseable calendar (regenerated each run) |
| `archive.json` | `_update_archive()` | Machine-readable edition metadata |

These are generated files — don't edit them manually. The pipeline regenerates them on every run.

---

## Next Steps

- How all files connect → **[Architecture Overview](02-architecture-overview.md)**
- Setting up your development environment → **[Environment Setup](04-environment-setup.md)**
- API keys and secrets → **[API Keys & Secrets](05-api-keys-and-secrets.md)**

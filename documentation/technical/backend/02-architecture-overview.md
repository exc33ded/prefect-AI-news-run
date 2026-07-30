# Architecture Overview

This page explains the high-level architecture of The AI Herald. By the end, you'll understand every component, how they connect, and the decisions that shaped them.

---

## System Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│                     THE AI HERALD SYSTEM                         │
│                                                                 │
│  ┌─────────────────┐   ┌──────────────────┐   ┌──────────────┐ │
│  │  Prefect Cloud   │   │   External APIs   │   │    GitHub     │ │
│  │  (Orchestrator)  │   │                   │   │   (Output)    │ │
│  │                  │   │  • Tavily Search  │   │               │ │
│  │  ┌────────────┐  │   │  • DeepSeek AI    │   │  • Pages Host │ │
│  │  │ Schedule   │  │   │  • Groq AI        │   │  • Archive DB │ │
│  │  │ (cron)     │  │   │  • Resend Email   │   │  • Edition    │ │
│  │  └─────┬──────┘  │   │  • GitHub API     │   │    Storage    │ │
│  │        │         │   │                   │   │               │ │
│  │  ┌─────▼──────┐  │   └────────▲─────────┘   └───────▲───────┘ │
│  │  │ Flow Run   │  │            │                      │         │
│  │  │ (container)│──┼────────────┼──────────────────────┘         │
│  │  └────────────┘  │            │                                │
│  │                  │            │                                │
│  │  • Secret Store  │            │                                │
│  │    (API keys)    │────────────┘                                │
│  └─────────────────┘                                             │
│                                                                 │
│                          ┌──────────────┐                       │
│                          │   Recipient   │                       │
│                          │   (Inbox)     │                       │
│                          └──────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

The system has three external boundaries:
1. **Prefect Cloud** — orchestrates execution, stores secrets, provides the schedule
2. **External APIs** — Tavily (search), DeepSeek/Groq (AI), Resend (email), GitHub (publishing)
3. **GitHub** — stores the code, hosts the output (GitHub Pages), acts as an archive database

---

## Component Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│  flow.py (Orchestrator)                                           │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                   daily_ai_digest @flow                     │ │
│  │                                                             │ │
│  │  1. submit_all_searches()  ──→  10 parallel Tavily searches  │ │
│  │         │                     (search.py)                    │ │
│  │         ▼                                                    │ │
│  │  2. process_results()      ──→  DeepSeek/Groq summarization  │ │
│  │         │                     (process.py)                   │ │
│  │         ▼                                                    │ │
│  │  3. render_email()         ──→  Jinja2 email template        │ │
│  │         │                     (format_email.py)              │ │
│  │         ├─────────────────────────────────────────┐          │ │
│  │         │                                         │          │ │
│  │         ▼                                         ▼          │ │
│  │  4a. send_email()       4b. render_page()                    │ │
│  │      (notify.py)            (format_page.py)                 │ │
│  │      • Resend API           • Jinja2 edition template         │ │
│  │                             │                                │ │
│  │                       4c. fetch_archive_editions()           │ │
│  │                           (publish_github.py)                │ │
│  │                           • GitHub Contents API GET          │ │
│  │                             │                                │ │
│  │                             ▼                                │ │
│  │                      4d. publish_page()                      │ │
│  │                           (publish_github.py)                │ │
│  │                           • PUT index.html                   │ │
│  │                           • PUT {date}.html                  │ │
│  │                           • UPDATE archive.json              │ │
│  │                           • RENDER archive.html              │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  config.py    ←  loads secrets (.env / Prefect blocks)           │
│  categories.py ← defines 10 search categories                     │
│  templates/   ←  Jinja2 HTML templates (email + edition + archive) │
└───────────────────────────────────────────────────────────────────┘
```

---

## Data Flow (Detailed)

### Stage 1: Search

```
categories.py           config.py
     │                      │
     ▼                      ▼
10 × search_category(task) ← secrets (Tavily keys)
     │
     ├── repos → "new AI tools GitHub 2026"
     ├── skills → "new AI agent skills 2026"
     ├── prompting → "prompt engineering best practices 2026"
     ├── papers → "AI research papers 2026"
     ├── startups → "AI startup funding news 2026"
     ├── model_releases → "new AI models released today 2026"
     ├── benchmarks → "AI benchmark results 2026"
     ├── industry_news → "AI industry developments 2026"
     ├── trends → "emerging AI trends 2026"
     └── productivity → "AI productivity tools 2026"
     │
     ▼ (parallel execution via .submit())
     │
raw_by_category = {
    "repos": [{title, url, snippet, published_date}, ...],
    "skills": [...],
    ...
}
```

### Stage 2: Processing

```
raw_by_category
     │
     ▼
_index_raw() → assigns positional IDs
     │
[{id: 0, title, url}, {id: 1, title, url}, ...]
     │
     ▼
LLM prompt (DeepSeek):
  "For category 'repos', pick the most relevant items by id.
   Return JSON: [{id: int, summary: str}]
   NEVER write titles or URLs."
     │
     ▼
LLM response:
  [{id: 3, summary: "A new open-source framework..."},
   {id: 7, summary: "GitHub released..."}]
     │
     ▼
_resolve_picks() → pulls titles/URLs from raw data by id
     │
digest = {
    "repos": [
        {title: "...", summary: "...", url: "...", source_name: "github.com"},
        ...
    ],
    ...
}
```

### Stage 3: Rendering & Delivery

```
digest ──┬──→ render_email(digest, edition_url)
         │        │
         │        ▼
         │    templates/email.html (Jinja2)
         │        │
         │        ▼
         │    HTML email string
         │        │
         │        ▼
         │    send_email(html)
         │        │
         │        ▼ Resend API
         │    Recipient's inbox
         │
         ├──→ fetch_archive_editions()
         │        │
         │        ▼ GitHub Contents API
         │    docs/archive.json (list of past editions)
         │
         └──→ render_page(digest, editions)
                  │
                  ▼
              templates/edition.html (Jinja2)
                  │
                  ▼
              (html, meta: {date, vol, no, category_counts, lead_story})
                  │
                  ▼
              publish_page(html, editions, meta)
                  │
                  ├──→ PUT docs/index.html
                  ├──→ PUT docs/{date}.html
                  ├──→ PUT docs/archive.json (updated)
                  └──→ PUT docs/archive.html (regenerated)
```

---

## Key Architectural Patterns

### Pattern 1: Isolation by Stage

Every stage after search is wrapped in its own try/except:

```python
# In flow.py
try:
    page_html, meta = render_page(digest, editions)
except Exception as e:
    print(f"Page rendering failed (continuing): {e}")
    page_html = None

try:
    send_email(email_html, date_str)
except Exception as e:
    print(f"Email delivery failed (continuing): {e}")
```

**Why:** Failure isolation. A rendering bug doesn't kill email delivery. An email delivery failure doesn't block publishing. Each stage is independent.

### Pattern 2: Dual Secret Source

```python
# In config.py
def get_secret(name: str) -> Optional[str]:
    # Try environment first (local dev)
    value = os.getenv(name)
    if value:
        return value

    # Try Prefect blocks (Prefect Cloud)
    try:
        block_name = name.lower().replace("_", "-")
        block = Secret.load(block_name)
        return block.get()
    except Exception:
        return None
```

**Why:** Same code path for both local and cloud. No `if LOCAL: ... elif CLOUD: ...` branching. The `.env` file is for development; Prefect blocks are for production. Both are transparent to the calling code.

### Pattern 3: Id-Based LLM Interaction

```python
# LLM sees only IDs
prompt = "Pick by id: [{id: 0}, {id: 1}, {id: 2}, ...]"

# LLM responds with IDs + summaries
response = [{"id": 0, "summary": "..."}, {"id": 2, "summary": "..."}]

# Code resolves IDs to real data
for pick in response:
    real = indexed_raw[pick["id"]]
    result.append({"title": real["title"], "url": real["url"], ...})
```

**Why:** Anti-hallucination. The LLM cannot invent headlines or URLs because it never sees them. It only sees positional identifiers and writes summaries. All factual data (title, URL, source, date) comes from the original search results.

### Pattern 4: Sequential Key Rotation

```python
def _tavily_keys() -> list[str]:
    keys = []
    for i in range(1, 11):
        key = get_secret(f"TAVILY_API_KEY_{i}")
        if key:
            keys.append(key)
    return keys

def _search_with_fallback(query, keys):
    for key in keys:
        try:
            return search(query, api_key=key)
        except Exception:
            continue  # try next key
    return []  # all keys exhausted
```

**Why:** Resilience against API key rate limits or expiry. Up to 10 keys tried sequentially. If key 1 is rate-limited, key 2 picks up. Free Tavily accounts have 1,000 searches/month — with 10 keys, you get 10,000/month. The pipeline uses ~300/month (10 searches × 30 days), so even a single key is typically enough.

### Pattern 5: Template-Driven Output

```python
# All visual output goes through Jinja2 templates
env = Environment(loader=PackageLoader("daily_ai_digest", "templates"))
template = env.get_template("edition.html")
html = template.render(
    date=date_str,
    vol=volume,
    lead_story=lead,
    sections=sections,
    ...
)
```

**Why:** Separation of concerns. Python code handles data; templates handle presentation. Changing the look of the email or website doesn't require touching any pipeline code. Designers can modify HTML/CSS independently.

---

## Deployment Architecture

```
                    LOCAL DEV                     PREFTECT CLOUD
                    ─────────                     ──────────────

    uv sync                 uv export          prefect deploy
       │                        │                    │
       ▼                        ▼                    ▼
  .venv/               requirements.txt      ┌─────────────────┐
  (all deps)           (pip-locked deps)     │ Prefect Cloud   │
       │                        │            │                 │
       │                        │            │ Work Pool:      │
       ▼                        │            │ ai-digest-      │
  uv run python main.py ────────┘            │ managed-pool    │
       │                                     │                 │
       ▼                                     │ Deployment:     │
  .env ──→ secrets    ───── (separate) ────→ │ daily-ai-digest │
       │                                     │                 │
       ▼                                     │ Schedule:       │
  Local execution                             │ 0 8 * * * IST   │
                                              │                 │
                                              │ Secrets:        │
                                              │ Secret blocks   │
                                              └────────┬────────┘
                                                       │
                                                       ▼
                                              Managed container
                                              ┌──────────────┐
                                              │ git clone    │
                                              │ pip install  │
                                              │ flow run     │
                                              └──────────────┘
```

### The uv → pip Bridge

```
pyproject.toml  →  uv.lock  →  uv export  →  requirements.txt  →  Prefect Cloud
      │               │                          │
  (dev deps)     (pinned)                  (no dev deps,
  (editable)     (hashed)                  no editable,
                                          pip-compatible)
```

1. `uv sync` — local development (fast, cached, includes dev tools)
2. `uv.lock` — canonical resolution (checked into git, ensures reproducible builds)
3. `uv export --frozen --no-dev --no-editable -o requirements.txt` — generates pip-compatible lockfile
4. Prefect Cloud reads `requirements.txt` via `pip_install_requirements` pull step

**Why not use uv on Prefect Cloud?** Prefect's managed work pool provides a container with a standard Python + pip image. Using pip lets us work within that constraint. If Prefect adds uv support to managed pools, we'd switch.

---

## Failure Modes and Recovery

| Failure | Behavior | Recovery |
|---------|----------|----------|
| Single category search fails | Returns `[]`, other categories continue | Automatic — no action needed |
| All searches fail | Empty raw results → empty digest | Pipeline still completes; email shows "no results" |
| DeepSeek API fails | Falls back to Groq automatically | Automatic — handled in `process.py` |
| Both LLMs fail | Returns `_empty_digest()` — raw results, no summaries | Manual — both providers are typically not down simultaneously |
| Email fails | Stage isolated — publishing still happens | Check Resend API status; pipeline logs the error |
| GitHub publishing fails | Stage isolated — email still sends | Check GitHub token/API; pipeline logs the error |
| Container crashes mid-flow | Prefect retries the entire flow (if configured) | Automatic — see deployment config |
| Secret not found | `get_secret()` returns `None`, code handles gracefully | Add the missing secret to Prefect Cloud or `.env` |

---

## Performance Characteristics

| Metric | Typical Value | Notes |
|--------|--------------|-------|
| Search phase | 10-20 seconds | 10 parallel searches; dominated by Tavily API latency |
| LLM processing | 5-10 seconds | Single LLM call with all results; dominated by model inference time |
| Email rendering | <1 second | Jinja2 template is cached after first render |
| Page rendering | <1 second | Jinja2 template is cached after first render |
| Email delivery | 2-5 seconds | Resend API roundtrip |
| GitHub publishing | 3-8 seconds | 3-4 API calls (index, edition, archive.json, archive.html) |
| **Total flow** | **30-60 seconds** | Parallel execution of independent stages could reduce this |

**Bottleneck:** Tavily search (~15 seconds for 10 parallel requests). This is network-bound, not CPU-bound. Running more Tavily keys in parallel wouldn't help — the limit is per-account API latency.

---

## Next Steps

- For a file-by-file walkthrough → **[Project Structure](03-project-structure.md)**
- To understand how secrets work → **[API Keys & Secrets](05-api-keys-and-secrets.md)**
- To understand the search pipeline → **[Search Pipeline](08-search-pipeline.md)**
- To understand LLM processing → **[LLM Processing Pipeline](09-llm-processing-pipeline.md)**

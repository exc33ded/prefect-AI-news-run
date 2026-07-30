# Search Pipeline

How the pipeline searches for AI news — the Tavily integration, parallel execution, key rotation, result normalization, and freshness filtering.

---

## Overview

The search pipeline performs **10 parallel searches** using the Tavily API, one per category. Each search is a separate Prefect task submitted via `.submit()` for concurrent execution. If one category fails, the others continue. If a Tavily API key hits a rate limit, the next key in the rotation takes over.

```
CATEGORIES (categories.py)
  │
  ├── repos
  ├── skills
  ├── prompting
  ├── papers
  ├── startups
  ├── model_releases
  ├── benchmarks
  ├── industry_news
  ├── trends
  └── productivity
  │
  ▼
submit_all_searches()
  │
  ├── search_category.submit("repos", ...)      ─┐
  ├── search_category.submit("skills", ...)      │
  ├── search_category.submit("prompting", ...)   │  Parallel
  ├── search_category.submit("papers", ...)      │  execution
  ├── ... 10 total ...                           │  via .submit()
  └── search_category.submit("productivity", ...)─┘
  │
  ▼
raw_by_category = {key: [results], ...}
```

---

## Key Functions

### `submit_all_searches()`

Launches all 10 searches concurrently:

```python
def submit_all_searches():
    futures = {}
    for cat in CATEGORIES:
        future = search_category.submit(cat["key"], cat["label"], cat["query"])
        futures[cat["key"]] = future
    return futures
```

**`.submit()` behavior:** Returns immediately with a future. The task runs in the background. The flow collects results later by calling `.result()` on each future.

---

### `search_category()` — The Task

```python
@task
def search_category(key: str, label: str, query: str) -> list[dict]:
    keys = _tavily_keys()
    results = _search_with_fallback(query, keys)
    return _normalize(results, key)
```

**Three steps:**
1. Get available Tavily API keys
2. Search with fallback (try keys sequentially)
3. Normalize results to standard format

---

### `_tavily_keys()` — Key Discovery

```python
def _tavily_keys() -> list[str]:
    keys = []
    for i in range(1, 11):  # TAVILY_API_KEY_1 through TAVILY_API_KEY_10
        key = get_secret(f"TAVILY_API_KEY_{i}")
        if key:
            keys.append(key)
        else:
            break  # Stop at first missing key
    return keys
```

**Design decision:** Stops at the first missing key, rather than checking all 10 slots. This means keys must be sequential — if you have keys 1, 2, and 4, key 4 is ignored.

---

### `_search_with_fallback()` — Key Rotation

```python
def _search_with_fallback(query: str, keys: list[str]) -> list:
    for key in keys:
        try:
            client = TavilyClient(api_key=key)
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=10
            )
            return response.get("results", [])
        except Exception as e:
            print(f"Tavily key failed ({key[:8]}...): {e}")
            continue  # Try next key
    return []  # All keys exhausted
```

**What happens:**
1. Try key 1 → if rate-limited, move to key 2
2. Try key 2 → if rate-limited, move to key 3
3. ... continue until a key works or all are exhausted
4. If all fail: return `[]` (empty) — the category appears with "no results found"

**Why sequential, not parallel?** Free Tavily keys have rate limits measured per key, not globally. Sequential retry maximizes the chance of a successful request without consuming all keys' quotas simultaneously. If all keys fail simultaneously, it's likely a Tavily outage, not a rate limit issue.

---

### `_normalize()` — Result Standardization

```python
def _normalize(results: list, category_key: str) -> list[dict]:
    normalized = []
    for r in results:
        normalized.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": r.get("content", "")[:500],
            "published_date": r.get("published_date", ""),
            "source_name": _extract_source(r.get("url", "")),
        })
    return normalized
```

**What happens:**
- `title` → direct from Tavily
- `url` → direct from Tavily
- `snippet` → truncated to 500 chars (prevents overly long raw text from bloating the LLM prompt)
- `published_date` → direct from Tavily (when available)
- `source_name` → extracted from URL (e.g., `github.com` from `https://github.com/user/repo`)

---

### `_github_repo_age_days()` — Repo Freshness

For the `repos` category only, the pipeline checks how old each GitHub repository is:

```python
def _github_repo_age_days(url: str) -> Optional[int]:
    # Extract owner/repo from GitHub URL
    # Example: https://github.com/vercel/ai → vercel/ai
    match = re.search(r"github\.com/([^/]+/[^/]+)", url)
    if not match:
        return None  # Not a GitHub URL, skip filtering

    repo_full = match.group(1).rstrip("/")
    api_url = f"https://api.github.com/repos/{repo_full}"

    resp = httpx.get(api_url)
    if resp.status_code != 200:
        return None  # API failure, skip filtering (fail-open)

    created_at = resp.json().get("created_at")
    created_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - created_date).days
```

**Key design: Fail-open.** If the GitHub API call fails for any reason, the function returns `None`. The filter treats `None` as "don't know, don't filter." This ensures that GitHub API outages don't block news delivery.

---

### `_filter_stale_repos()` — 90-Day Threshold

```python
STALE_REPO_DAYS = 90

def _filter_stale_repos(results: list[dict]) -> list[dict]:
    fresh = []
    for r in results:
        if "github.com" not in r.get("url", ""):
            fresh.append(r)  # Non-GitHub results pass through
            continue
        age_days = _github_repo_age_days(r["url"])
        if age_days is None or age_days <= STALE_REPO_DAYS:
            fresh.append(r)  # Unknown age or fresh enough
    return fresh
```

**Three outcomes:**
1. **Non-GitHub URL** → kept (no filtering needed)
2. **GitHub URL, age ≤ 90 days** → kept (fresh)
3. **GitHub URL, age > 90 days** → removed (stale)
4. **GitHub URL, API fails to get age** → kept (fail-open)

---

## Search Queries

Each category has a search query defined in `categories.py`. The queries follow a pattern:

```python
CATEGORIES = [
    {"key": "repos",         "query": "new AI tools released today 2026 GitHub repository"},
    {"key": "skills",        "query": "new AI agent skills extensions plugins 2026"},
    {"key": "prompting",     "query": "prompt engineering best practices techniques 2026"},
    {"key": "papers",        "query": "latest AI research papers published today 2026 arxiv"},
    {"key": "startups",      "query": "AI startup funding news announcements 2026"},
    {"key": "model_releases","query": "new AI models released today 2026 open source commercial"},
    {"key": "benchmarks",    "query": "AI benchmark results leaderboard 2026"},
    {"key": "industry_news", "query": "AI industry developments partnerships policy 2026"},
    {"key": "trends",        "query": "emerging AI trends predictions 2026"},
    {"key": "productivity",  "query": "AI productivity tools software 2026"},
]
```

**Query design principles:**
- Include the current year (`2026`) to bias toward recency
- Use terms the search engine associates with "new/fresh" content: "released today," "latest," "new," "emerging"
- Be specific enough to avoid generic results but broad enough to catch different sub-topics

---

## Execution Flow (Detailed)

```
submit_all_searches()
  │
  ├─→ search_category.submit("repos", "repos", "new AI tools...")
  │     │
  │     ├─ _tavily_keys() → ["tvly-abc", "tvly-def"]
  │     ├─ _search_with_fallback("new AI tools...", ["tvly-abc", "tvly-def"])
  │     │     │
  │     │     ├─ Try key "tvly-abc" → ✅ Success (10 results)
  │     │     └─ Return results
  │     │
  │     ├─ _normalize(results, "repos") → [{title, url, snippet, date, source}, ...]
  │     └─ _filter_stale_repos(normalized) → filter out repos > 90 days old
  │
  ├─→ search_category.submit("skills", ...)    [runs simultaneously]
  ├─→ search_category.submit("prompting", ...) [runs simultaneously]
  └─→ ... 7 more ...
  │
  ▼
Result collection (in flow.py):
  for key, future in futures.items():
      try:
          raw_by_category[key] = future.result()
      except Exception as e:
          print(f"Search failed for {key}: {e}")
          raw_by_category[key] = []
```

**What returns:**
```python
raw_by_category = {
    "repos": [
        {
            "title": "New AI CLI tool released",
            "url": "https://github.com/user/repo",
            "snippet": "A new CLI tool for...",
            "published_date": "2026-01-30",
            "source_name": "github.com"
        },
        ...
    ],
    "skills": [...],
    ...
}
```

---

## Failure Modes

| Failure | Behavior | Visible In Digest As |
|---------|----------|---------------------|
| Single Tavily key rate-limited | Try next key in rotation | (invisible — automatic recovery) |
| All Tavily keys exhausted | Return `[]` for that category | Category section with "(no results)" |
| Github API down (repo age check) | All GitHub URLs kept (fail-open) | Potentially older repos included |
| Single category search completely fails | Exception caught, `[]` assigned | That category omitted or shows "(no results)" |
| Tavily API down entirely | All categories fail, empty digest | Digest shows "no news found today" |

---

## Performance

- **Parallel execution:** 10 searches run concurrently, not sequentially. Total time ≈ slowest individual search (~3-5 seconds), not 10 × individual time.
- **Tavily latency:** ~1-3 seconds per search request (advanced search depth)
- **GitHub API calls:** ~2-5 seconds per repo (only for repos category, only for GitHub URLs)
- **Key rotation latency:** Negligible (fails fast when rate-limited)

**Typical search phase:** 10-20 seconds (dominated by network latency to Tavily and GitHub APIs).

---

## Modifying the Search

### Adding a Category

Edit `categories.py`:

```python
CATEGORIES = [
    # ... existing categories ...
    {
        "key": "robotics",
        "label": "🤖 Robotics",
        "query": "AI robotics breakthroughs 2026"
    },
]
```

That's it. The new category propagates automatically through search → processing → rendering → email. No other files need changes.

### Adding More Tavily Keys

In `.env` (local) or as Prefect blocks:

```bash
TAVILY_API_KEY_1=tvly-abc
TAVILY_API_KEY_2=tvly-def
TAVILY_API_KEY_3=tvly-ghi  # New key
TAVILY_API_KEY_4=tvly-jkl  # New key
```

Keys must be sequential (no gaps).

### Changing the Stale Repo Threshold

In `search.py`:

```python
STALE_REPO_DAYS = 60  # Change from 90 to 60 days
```

### Changing Search Depth

In `_search_with_fallback()`:

```python
response = client.search(
    query=query,
    search_depth="basic",   # Change from "advanced" to "basic" (faster, less thorough)
    max_results=5           # Change from 10 to 5 (fewer results)
)
```

---

## Next Steps

- How results are summarized → **[LLM Processing Pipeline](09-llm-processing-pipeline.md)**
- How results become HTML → **[Edition Template](../../frontend/19-edition-template.md)**
- Adding new features → **[Extending the System](14-extending-the-system.md)**

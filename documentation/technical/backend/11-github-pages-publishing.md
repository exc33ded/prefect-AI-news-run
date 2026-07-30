# GitHub Pages Publishing

How the web edition gets published — the GitHub Contents API integration, archive management, and the complete file lifecycle on every run.

---

## Overview

The publishing pipeline writes the rendered HTML to GitHub via the Contents API. On every run, four files are created or updated: the live `index.html`, a permanent `{date}.html` archive edition, the machine-readable `archive.json`, and the browseable `archive.html` calendar page.

```
rendered page (HTML) + meta (date, vol, issue, ...)
  │
  ▼
publish_page(html, editions, meta)  ← @task in publish_github.py
  │
  ├── GET existing docs/index.html SHA
  ├── PUT docs/index.html (overwrite — latest edition)
  ├── PUT docs/{date}.html (create — permanent archive)
  ├── _update_archive(editions, meta)
  │     ├── Append new edition to archive list
  │     ├── PUT docs/archive.json (updated metadata)
  │     └── Render archive.html → PUT docs/archive.html
  └── Done
```

---

## Key Functions

### `publish_page()` — The Main Task

```python
@task
def publish_page(page_html: str, editions: list[dict], meta: dict):
    token = get_secret("GITHUB_TOKEN")
    repo = get_secret("GITHUB_REPO")

    if not token or not repo:
        print("GitHub publishing skipped (missing token/repo)")
        return

    client = httpx.Client(
        base_url=f"https://api.github.com/repos/{repo}/contents/",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ai-herald/1.0",
        },
    )

    date_str = meta["date"]

    # 1. Update index.html (latest edition)
    _put_file(client, "docs/index.html", page_html)

    # 2. Create permanent archive edition
    _put_file(client, f"docs/{date_str}.html", page_html)

    # 3. Update archive
    _update_archive(client, editions, meta)
```

**Why separate index + date files?**
- `docs/index.html` is always the latest edition — GitHub Pages serves it at the root URL
- `docs/{date}.html` are permanent — historical editions are never deleted
- Both use identical HTML content

---

### `_put_file()` — File Upload

```python
def _put_file(client: httpx.Client, path: str, content: str):
    # Get current SHA (if file exists)
    resp = client.get(f"docs/{path}")
    sha = resp.json().get("sha") if resp.status_code == 200 else None

    # Encode content
    content_b64 = base64.b64encode(content.encode()).decode()

    # Build request body
    body = {
        "message": f"Update {path}",
        "content": content_b64,
    }
    if sha:
        body["sha"] = sha  # Required for updates

    # PUT to GitHub
    resp = client.put(path, json=body)
    if resp.status_code in (200, 201):
        print(f"  Published: {path}")
    else:
        print(f"  Failed: {path} ({resp.status_code})")
        print(f"  {resp.json().get('message', 'Unknown error')}")
```

**SHA-based update pattern:**
- **Create** (file doesn't exist): Omit `sha` from the request body. GitHub creates the file.
- **Update** (file exists): Include current `sha` from a GET request. GitHub uses it for conflict detection — if someone else updated the file between your GET and PUT, the PUT fails.

**This is GitHub's Contents API requirement** — all updates must include the SHA of the file being replaced. Without it, GitHub returns 409 Conflict.

---

### `fetch_archive_editions()` — Reading History

```python
@task
def fetch_archive_editions() -> list[dict]:
    token = get_secret("GITHUB_TOKEN")
    repo = get_secret("GITHUB_REPO")

    if not token or not repo:
        return []

    client = httpx.Client(
        base_url=f"https://api.github.com/repos/{repo}/contents/",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        },
    )

    resp = client.get("docs/archive.json")
    if resp.status_code == 200:
        content_b64 = resp.json().get("content", "")
        content = base64.b64decode(content_b64).decode()
        return json.loads(content)

    return []  # No archive yet (first run)
```

**What it returns:**
```json
[
  {
    "date": "2026-01-28",
    "vol": "I",
    "issue": 1,
    "lead_story": "OpenAI Releases GPT-5",
    "category_count": 10
  },
  {
    "date": "2026-01-29",
    "vol": "I",
    "issue": 2,
    "lead_story": "New AI Chip Architecture",
    "category_count": 9
  }
]
```

This is used to:
1. Calculate the next Volume/Issue number
2. Generate the archive page (calendar grid showing all past editions)
3. Provide historical context for the current edition

---

### `_update_archive()` — Archive Maintenance

```python
def _update_archive(client: httpx.Client, editions: list[dict], meta: dict):
    # Append new edition
    editions.append({
        "date": meta["date"],
        "vol": meta["vol"],
        "issue": meta["issue"],
        "lead_story": meta["lead_story"],
        "category_count": meta["category_count"],
    })

    # Write updated archive.json
    archive_json = json.dumps(editions, indent=2)
    _put_file(client, "docs/archive.json", archive_json)

    # Render and write archive.html
    archive_html = _render_archive(editions)
    _put_file(client, "docs/archive.html", archive_html)
```

### `_render_archive()` — Archive Page Generation

```python
def _render_archive(editions: list[dict]) -> str:
    env = Environment(loader=PackageLoader("daily_ai_digest", "templates"))
    template = env.get_template("archive.html")

    # Group by year/month for the calendar
    calendar = {}
    for edition in editions:
        year_month = edition["date"][:7]  # "2026-01"
        if year_month not in calendar:
            calendar[year_month] = []
        calendar[year_month].append(edition)

    return template.render(calendar=calendar, editions=editions)
```

---

## Complete File Lifecycle Per Run

```
RUN START
  │
  ├── fetch_archive_editions()
  │     └── GET docs/archive.json → editions list
  │
  ├── publish_page(html, editions, meta)
  │     │
  │     ├── GET docs/index.html  → SHA
  │     └── PUT docs/index.html  → Latest edition (OVERWRITE)
  │     │
  │     └── PUT docs/{date}.html → Permanent archive (CREATE)
  │     │
  │     └── _update_archive(editions, meta)
  │           │
  │           ├── editions.append(new_edition)
  │           │
  │           ├── PUT docs/archive.json  → Updated metadata (OVERWRITE)
  │           │
  │           └── _render_archive(editions)
  │                 │
  │                 └── PUT docs/archive.html  → Updated calendar (OVERWRITE)
  │
  └── RUN COMPLETE
```

---

## GitHub Pages Configuration

### How GitHub Pages Serves `docs/`

GitHub Pages is configured to serve from the `/docs` folder on the `main` branch:

1. **Repository Settings → Pages**
2. **Source:** Deploy from a branch
3. **Branch:** `main` → `/docs`
4. **Custom domain:** (optional)

**URL mapping:**
| File Path | URL |
|-----------|-----|
| `docs/index.html` | `https://username.github.io/repo/` |
| `docs/2026-01-30.html` | `https://username.github.io/repo/2026-01-30.html` |
| `docs/archive.html` | `https://username.github.io/repo/archive.html` |
| `docs/archive.json` | `https://username.github.io/repo/archive.json` |

### Build and Deployment

GitHub Pages automatically builds and deploys when files in `docs/` change:
- Pipeline runs → writes to `docs/` via API → GitHub detects changes → Pages rebuilds → site updates
- Typical delay: 30 seconds to 2 minutes after the pipeline writes

---

## API Rate Limits

GitHub's Contents API has rate limits:

| Limit | Value | Pipeline Usage |
|-------|-------|---------------|
| Authenticated requests/hour | 5,000 | ~5-7 per run |
| Unauthenticated requests/hour | 60 | Not used (pipeline always authenticates) |
| File size limit | 100 MB | HTML files are ~50KB |

The pipeline uses 5-7 API calls per run:
- 1 GET for `archive.json`
- ~3 GETs for SHAs (index.html, date.html, archive.json, archive.html)
- ~4 PUTs (index.html, date.html, archive.json, archive.html)

At one run per day, that's ~210 requests/month — well within limits.

---

## Repository Structure After Multiple Runs

```
docs/
├── index.html          ← Latest edition (Jan 30, 2026)
├── 2026-01-28.html     ← Archive edition
├── 2026-01-29.html     ← Archive edition
├── 2026-01-30.html     ← Archive edition
├── archive.html        ← Browseable calendar (all editions)
├── archive.json        ← Machine-readable metadata
└── mockups/            ← Design exploration (not touched by pipeline)
    ├── 1-broadsheet.html
    ├── 2-tabloid.html
    ├── 3-financial.html
    └── archive-preview.html
```

Archive files accumulate forever. Consider periodic cleanup if storage becomes a concern (unlikely at ~50KB per edition).

---

## Volume/Issue Numbering

### `_volume_and_issue()`

```python
def _volume_and_issue(editions: list[dict]) -> tuple[str, int]:
    if not editions:
        return _to_roman(1), 1  # First edition ever

    # Find the first edition date
    first_date = datetime.fromisoformat(editions[0]["date"])

    # Calculate months since first edition
    today = datetime.now()
    months_diff = (today.year - first_date.year) * 12 + (today.month - first_date.month)
    volume_num = months_diff + 1  # Volume 1 for month 0

    # Count editions this month
    this_month = today.strftime("%Y-%m")
    issues_this_month = sum(
        1 for e in editions if e["date"].startswith(this_month)
    )
    issue_num = issues_this_month + 1  # This edition's number

    return _to_roman(volume_num), issue_num
```

**Example:** If the first edition was January 15, 2026 and today is March 5, 2026:
- Volume: III (months 0=Jan, 1=Feb, 2=Mar → months_diff=2 → volume=3 → Roman: III)
- Issue: depends on how many editions exist in March so far
  - If 4 editions in March → issue = 5
  - Result: **Vol. III, No. 5**

### `_to_roman()`

```python
def _to_roman(num: int) -> str:
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    roman_num = ""
    for i in range(len(val)):
        count = num // val[i]
        roman_num += syms[i] * count
        num -= val[i] * count
    return roman_num
```

Converts 1→I, 2→II, 3→III, 4→IV, 5→V, ... up to any positive integer.

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Missing `GITHUB_TOKEN` | Publishing skipped, flow continues |
| Missing `GITHUB_REPO` | Publishing skipped, flow continues |
| GET SHA fails (file doesn't exist) | SHA = None → create operation |
| PUT fails (conflict) | Error logged, flow continues |
| API rate limited | Error logged, flow continues |
| `archive.json` not found (first run) | Empty list → Volume I, Issue 1 |
| `archive.json` malformed | Empty list → Volume I, Issue 1 |

**Fail-open design:** All GitHub publishing failures are caught and logged. The email delivery (which happens in a separate, isolated stage) is unaffected.

---

## Troubleshooting

### "Website not updating after pipeline runs"

1. Check GitHub Pages build status: Repository → Actions → Pages build and deployment
2. Wait 1-2 minutes after the pipeline finishes — Pages has a delay
3. Hard refresh the browser (Ctrl+Shift+R or Cmd+Shift+R)
4. Check that `docs/index.html` was actually updated (view the file on GitHub)

### "403 Forbidden from GitHub API"

- `GITHUB_TOKEN` is invalid or expired → regenerate it
- Token doesn't have `repo` scope → create a new token with repo scope
- Repository is private and token lacks access → use a token with read/write access

### "409 Conflict on PUT"

Someone or something else modified the file between the GET (SHA fetch) and PUT (write). This is rare for a single-pipeline system. If it happens consistently, something else is writing to `docs/` (e.g., another pipeline deployment, manual edits).

### "File size too large"

Unlikely (~50KB HTML files). If it happens, reduce the template size or split into multiple files.

---

## Next Steps

- Understand the web page template → **[Edition Template](../../frontend/19-edition-template.md)**
- Understand the archive template → **[Archive Template](../../frontend/21-archive-template.md)**
- How errors are handled across the system → **[Resilience & Error Handling](15-resilience-and-errors.md)**

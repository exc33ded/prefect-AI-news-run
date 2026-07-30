# Extending the System

Recipes for common modifications — adding categories, changing providers, customizing templates, and more. Each recipe is a self-contained set of steps.

---

## Add a New Search Category

The most common extension. Adding a category propagates automatically through search → LLM → email → website.

**Edit `daily_ai_digest/categories.py`:**

```python
CATEGORIES = [
    # ... existing categories ...
    {
        "key": "robotics",
        "label": "🤖 Robotics",
        "query": "AI robotics breakthroughs humanoid robots 2026"
    },
]
```

**That's it.** No other files need changes. The category appears in:
- Search (automatically — `submit_all_searches()` iterates `CATEGORIES`)
- LLM processing (automatically — `process_results()` iterates category keys)
- Email (automatically — `render_email()` iterates `CATEGORIES`)
- Website (automatically — `render_page()` iterates digest keys)

**Re-deploy:**

```bash
uv export --frozen --no-dev --no-editable -o requirements.txt
git add . && git commit -m "Add robotics category" && git push
prefect deploy --name daily-ai-digest
```

---

## Remove a Category

Delete the entry from `categories.py`. The rest of the pipeline adapts automatically.

---

## Change the LLM Provider

### Switch to OpenAI

**Edit `daily_ai_digest/process.py`:**

```python
def _build_openai_client(provider="openai"):
    if provider == "openai":
        return OpenAI(
            api_key=get_secret("OPENAI_API_KEY"),
            # base_url default = https://api.openai.com/v1
        )
    # ... fallback provider ...
```

Update the model name in `_call_llm()`:

```python
model = "gpt-4o-mini"
```

### Switch to Anthropic (via proxy)

```python
client = OpenAI(
    api_key=get_secret("ANTHROPIC_API_KEY"),
    base_url="https://api.anthropic.com/v1",  # OpenAI-compatible proxy
)
model = "claude-3-haiku-20240307"
```

### Add a Third Provider

Extend the fallback chain in `process_results()`:

```python
try:
    # Primary: DeepSeek
    digest = _call_and_resolve(_build_openai_client("deepseek"), indexed)
except Exception as e1:
    try:
        # Fallback 1: Groq
        digest = _call_and_resolve(_build_openai_client("groq"), indexed)
    except Exception as e2:
        try:
            # Fallback 2: Your new provider
            digest = _call_and_resolve(_build_openai_client("custom"), indexed)
        except Exception as e3:
            # Last resort: empty digest
            digest = _empty_digest(categories)
```

---

## Change the Number of Stories Per Category

**Edit the system prompt in `_build_system_prompt()`:**

```python
# More stories (5-8 per category)
"select the 5-8 most significant items"

# Fewer stories (1-2 per category) — tighter digest
"select the 1-2 most significant items"
```

**Also adjust email display in `format_email.py`:**

```python
top_three[key] = items[:3]  # instead of items[:2]
```

---

## Change the Email Look

**Edit `daily_ai_digest/templates/email.html`.**

### Change Colors

```html
<!-- Masthead background -->
<td style="background-color: #1a1a2e; padding: 30px;">
    <!-- Dark navy instead of red -->
</td>
```

### Change Fonts

```html
<!-- Modern sans-serif instead of serif -->
<td style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; ...">
```

### Add a Logo

```html
<!-- Before the masthead -->
<img src="https://yourdomain.com/logo.png" alt="AI Herald" style="width: 80px; height: auto;">
```

**Important:** Email HTML is fragile. Test in multiple clients (Gmail, Outlook, Apple Mail) after changes. Inline CSS only.

---

## Change the Website Look

**Edit `daily_ai_digest/templates/edition.html`.**

### Change Theme Colors

CSS variables are at the top of the template:

```css
:root {
    --bg-primary: #f4e4c1;       /* Parchment background */
    --text-primary: #2c1810;     /* Dark brown text */
    --accent: #8b0000;           /* Deep red */
    --border: #8b7355;           /* Warm brown border */
}
```

### Change Layout

The template uses CSS Grid with specific column counts. Change `grid-template-columns` to adjust the layout:

```css
/* Default: 3-column sections */
.category-section {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 2rem;
}

/* Change to 2-column */
/* grid-template-columns: repeat(2, 1fr); */
```

### Add Social Sharing

Add OpenGraph meta tags in `<head>`:

```html
<meta property="og:title" content="The AI Herald — {{ date }}">
<meta property="og:description" content="Today's AI news, curated and summarized.">
<meta property="og:image" content="https://yourdomain.com/og-image.png">
```

---

## Change the Schedule

**Edit `prefect.yaml`:**

```yaml
schedules:
  - cron: "0 6 * * *"        # 6:00 AM instead of 8:00 AM
    timezone: "America/New_York"  # Eastern Time instead of IST
```

**Cron reference:**

| Expression | Meaning |
|-----------|---------|
| `0 8 * * *` | Every day at 8:00 AM |
| `0 8 * * 1-5` | Weekdays at 8:00 AM |
| `0 8 * * 0` | Sundays at 8:00 AM |
| `0 */6 * * *` | Every 6 hours |
| `0 8,20 * * *` | Twice a day (8 AM and 8 PM) |
| `30 7 * * *` | Every day at 7:30 AM |

**Re-deploy after changing:**

```bash
prefect deploy --name daily-ai-digest
```

---

## Add a Second Email Recipient

**Edit `daily_ai_digest/notify.py`:**

```python
params = {
    "from": get_secret("EMAIL_FROM") or "onboarding@resend.dev",
    "to": [
        get_secret("EMAIL_TO"),
        "colleague@example.com",
        "team@example.com",
    ],
    "subject": f"THE AI DAILY — {date_str}",
    "html": email_html,
}
```

**Free tier limitation:** Resend free tier only sends to the account email. To send to additional addresses, verify a domain.

---

## Add a Custom Search Filter

Example: filter out results from specific domains.

**Edit `daily_ai_digest/search.py` after `_normalize()`:**

```python
BLOCKED_DOMAINS = {"example.com", "spam-site.com"}

def _filter_blocked_domains(results: list[dict]) -> list[dict]:
    return [
        r for r in results
        if not any(domain in r["url"] for domain in BLOCKED_DOMAINS)
    ]
```

Call it in `search_category()`:

```python
@task
def search_category(key, label, query):
    results = _search_with_fallback(query, keys)
    normalized = _normalize(results, key)
    filtered = _filter_blocked_domains(normalized)  # New filter
    if key == "repos":
        filtered = _filter_stale_repos(filtered)
    return filtered
```

---

## Deploy to a Different Host

### Deploy to Netlify

Replace `publish_github.py` with a Netlify deploy hook:

```python
import httpx

def publish_page(html, meta):
    netlify_hook = get_secret("NETLIFY_DEPLOY_HOOK")
    # Write HTML to disk first, then trigger deploy
    with open(f"public/{meta['date']}.html", "w") as f:
        f.write(html)
    httpx.post(netlify_hook)
```

### Deploy to S3

```python
import boto3

def publish_page(html, meta):
    s3 = boto3.client("s3")
    s3.put_object(
        Bucket="your-bucket",
        Key=f"editions/{meta['date']}.html",
        Body=html,
        ContentType="text/html",
    )
```

---

## Add Analytics

Add to `templates/edition.html` in `<head>`:

```html
<!-- Plausible Analytics (privacy-friendly) -->
<script defer data-domain="yourdomain.com" src="https://plausible.io/js/script.js"></script>
```

Or Google Analytics:

```html
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

---

## Add Custom Pre-Commit Hooks

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

Install:

```bash
pre-commit install
```

---

## Next Steps

- Understanding error handling → **[Resilience & Error Handling](15-resilience-and-errors.md)**
- All commands → **[Command Cheatsheet](16-command-cheatsheet.md)**
- Fixing issues → **[Troubleshooting](17-troubleshooting.md)**

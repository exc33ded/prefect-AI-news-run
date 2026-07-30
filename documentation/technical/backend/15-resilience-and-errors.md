# Resilience & Error Handling

How the pipeline handles failures — the patterns, the philosophy, and how to add more resilience.

---

## Philosophy

The pipeline follows three principles:

1. **Never crash the whole pipeline for a partial failure.** Each stage is isolated. A search failure shouldn't block email. An email failure shouldn't block publishing.

2. **Fail open when possible.** If uncertain about something (e.g., a repo's age because GitHub API is down), include rather than exclude. An extra old repo in the digest is better than missing a new one.

3. **Always deliver something.** Even if every API fails, the digest is still generated. It just has fewer items. The user gets a digest, not an error.

---

## Error Isolation Architecture

```
┌──────────────────────────────────────────────────────────┐
│  daily_ai_digest @flow                                   │
│                                                          │
│  ┌─────────────┐                                         │
│  │ Search (10) │   Each category individually wrapped:   │
│  │             │   try: result = future.result()          │
│  │  repos      │   except: result = []                    │
│  │  skills     │   → One failure doesn't block others     │
│  │  ...        │                                         │
│  └─────────────┘                                         │
│        │                                                 │
│        ▼                                                 │
│  ┌─────────────────────┐                                 │
│  │ process_results()   │  try: DeepSeek                  │
│  │                     │  except: try Groq                │
│  │ @task(retries=2)    │  except: _empty_digest()         │
│  └─────────────────────┘                                 │
│        │                                                 │
│        ├─────────────────────────────────────┐            │
│        ▼                                     ▼            │
│  ┌──────────────────┐              ┌──────────────────┐  │
│  │ render_email()   │              │ render_page()    │  │
│  │ try: render      │              │ try: render      │  │
│  │ except: skip      │              │ except: skip     │  │
│  └──────────────────┘              └──────────────────┘  │
│        │                                     │            │
│        ▼                                     ▼            │
│  ┌──────────────────┐              ┌──────────────────┐  │
│  │ send_email()     │              │ publish_page()   │  │
│  │ @task(retries=2)  │              │ try: publish     │  │
│  │ try: send        │              │ except: skip     │  │
│  │ except: skip      │              └──────────────────┘  │
│  └──────────────────┘                                     │
│                                                          │
│  Every box = independent failure domain                   │
└──────────────────────────────────────────────────────────┘
```

---

## Error Handling Patterns

### Pattern 1: Per-Item Isolation (Search)

```python
# In flow.py — collecting search results
for key, future in futures.items():
    try:
        raw_by_category[key] = future.result()
    except Exception as e:
        print(f"Search failed for {key}: {e}")
        raw_by_category[key] = []  # Empty = no results for this category
```

**What happens:** If category "repos" fails but all others succeed, the pipeline continues with 9/10 categories. The failed category shows "(no results)" in the digest.

### Pattern 2: Provider Fallback (LLM)

```python
# In process.py — LLM summarization
try:
    client = _build_openai_client("deepseek")
    digest = _call_and_resolve(client, indexed)
except Exception as e1:
    try:
        client = _build_openai_client("groq")
        digest = _call_and_resolve(client, indexed)
    except Exception as e2:
        digest = _empty_digest(categories)
```

**What happens:** Three-tier fallback: DeepSeek → Groq → empty. Each failure narrows the quality of the output but never kills the pipeline.

### Pattern 3: Stage Isolation (Render/Deliver/Publish)

```python
# In flow.py — individually wrapped stages
try:
    email_html = render_email(digest, edition_url)
    send_email(email_html, date_str)
except Exception as e:
    print(f"Email stage failed: {e}")

try:
    page_html, meta = render_page(digest, editions)
    publish_page(page_html, editions, meta)
except Exception as e:
    print(f"Publishing stage failed: {e}")
```

**What happens:** If email fails but publishing succeeds, the website updates. If publishing fails but email succeeds, subscribers still get the digest. Two completely independent delivery paths.

### Pattern 4: Fail-Open (Repo Filtering)

```python
# In search.py — repo age check
age_days = _github_repo_age_days(url)
if age_days is None:  # API failed, unknown age
    fresh.append(r)    # Keep it (fail-open)
elif age_days <= STALE_REPO_DAYS:
    fresh.append(r)
# else: stale, removed
```

**What happens:** If GitHub API is down, all repos pass through. It's better to show an older repo than miss a new one.

### Pattern 5: Default Values (Missing Secrets)

```python
# In config.py
def get_secret(name):
    value = os.getenv(name)
    if value:
        return value
    try:
        return Secret.load(...).get()
    except:
        return None  # Missing = None, handled by caller
```

**What happens:** Missing secrets don't crash anything. Callers check for `None` and skip the feature:

```python
token = get_secret("GITHUB_TOKEN")
if not token:
    print("Publishing skipped (no token)")
    return  # Skip, don't crash
```

---

## Retry Strategy

### LLM Task

```python
@task(retries=2, retry_delay_seconds=[5, 15])
def process_results(raw_by_category):
    ...
```

- **Why 2 retries?** 3 total attempts (initial + 2 retries). Sufficient for transient failures.
- **Why 5s / 15s delays?** Exponential-ish backoff. First retry is quick (might be a blip). Second retry waits longer (might be a brief outage).
- **What triggers retry?** Any exception from the entire function, including both provider attempts.

### Email Task

```python
@task(retries=2, retry_delay_seconds=[5, 15])
def send_email(email_html, date_str):
    ...
```

Same strategy as LLM — 3 attempts with backoff.

### Search Task

```python
@task  # No retries at task level
def search_category(key, label, query):
    ...
```

**No retries at task level** — retries happen inside the function via key rotation. If all keys fail, the task returns `[]`. Retrying the entire task would just exhaust the keys again.

---

## Failure Modes Matrix

| Component | Failure | Effect | User-Visible |
|-----------|---------|--------|-------------|
| Tavily API | Single key rate-limited | Tries next key | Invisible |
| Tavily API | All keys exhausted | `[]` for that category | Category shows "(no results)" |
| Tavily API | API down (all categories) | Empty raw dict | Digest shows "no news found today" |
| GitHub API (repo age) | API down | All repos pass through | May include older repos |
| DeepSeek API | Auth/rate limit/network | Falls back to Groq | Invisible (same-quality summaries) |
| Groq API | Auth/rate limit/network (after DeepSeek fail) | Falls back to empty digest | Raw search results without summaries |
| Both LLMs | Both down simultaneously | `_empty_digest()` | Raw search results without summaries |
| Resend API | Auth/rate limit/network | Skips email after 2 retries | No email that day (but website updates) |
| GitHub Contents API | Auth/rate limit/network | Skips publishing | No website update (but email sends) |
| Prefect container | Crashes mid-flow | Prefect retries entire flow | Delayed digest (by retry time) |
| Missing secret | Secret block not found | Feature skipped | Depends on which secret (see below) |

---

## Recovery Time Objectives

| Severity | Scenario | Typical Recovery | Action Needed |
|----------|----------|-----------------|---------------|
| Minor | 1-2 Tavily keys rate-limited | Automatic (within same run) | None |
| Moderate | Single API provider down | Automatic (fallback within same run) | None |
| Major | Both LLMs down | Automatic (empty digest, raw results) | Monitor and wait |
| Critical | No secrets (complete misconfiguration) | Fails immediately | Fix secrets, re-run manually |
| Critical | Prefect Cloud outage | Schedule resumes when Cloud recovers | Wait for Prefect status update |

---

## Adding More Resilience

### Add Circuit Breakers

For repeated provider failures, track failure count and stop trying:

```python
class CircuitBreaker:
    def __init__(self, threshold=5, reset_seconds=300):
        self.failures = 0
        self.threshold = threshold
        self.reset_seconds = reset_seconds
        self.last_failure = None

    def call(self, fn):
        if self.failures >= self.threshold:
            if time.time() - self.last_failure < self.reset_seconds:
                raise Exception("Circuit breaker open")
            self.failures = 0  # Reset after timeout
        try:
            result = fn()
            self.failures = 0
            return result
        except Exception:
            self.failures += 1
            self.last_failure = time.time()
            raise
```

### Add Health Checks

Before the flow runs, verify critical services:

```python
@task
def health_check():
    # Check Tavily
    try:
        TavilyClient(api_key=get_secret("TAVILY_API_KEY_1")).search(
            query="test", max_results=1
        )
    except:
        print("WARNING: Tavily not healthy")

    # Check DeepSeek
    try:
        OpenAI(api_key=get_secret("OPENAI_API_KEY"),
               base_url="https://api.deepseek.com").models.list()
    except:
        print("WARNING: DeepSeek not healthy")
```

### Add Monitoring Hooks

Send alerts on repeated failures:

```python
# At the end of flow.py
if consecutive_failures >= 3:
    # Send alert via webhook/Discord/Slack
    httpx.post("https://hooks.slack.com/...", json={
        "text": f"⚠ AI Herald: {consecutive_failures} consecutive failures"
    })
```

---

## Debugging Failures

### Prefect Cloud Logs

Every `print()` in the flow appears in Prefect Cloud UI. Look for:
- `"Search failed for {key}: {error}"` — Tavily issue
- `"DeepSeek failed: {error}"` — LLM primary provider issue
- `"Groq also failed: {error}"` — Both LLM providers down
- `"Email stage failed: {error}"` or `"Publishing stage failed: {error}"` — Respective stage issues

### Secret Verification

```bash
# Check if secrets exist
prefect block ls | grep secret

# Test a specific secret (won't show value, just existence)
prefect block inspect secret/tavily-api-key-1
```

### API Testing

```bash
# Test Tavily
uv run python -c "
from daily_ai_digest.config import get_secret
from tavily import TavilyClient
c = TavilyClient(api_key=get_secret('TAVILY_API_KEY_1'))
print(c.search('test', max_results=1)['results'][0]['title'])
"

# Test DeepSeek
uv run python -c "
from daily_ai_digest.config import get_secret
from openai import OpenAI
c = OpenAI(api_key=get_secret('OPENAI_API_KEY'), base_url='https://api.deepseek.com')
print(c.chat.completions.create(model='deepseek-v4-flash', messages=[{'role':'user','content':'hi'}]).choices[0].message.content)
"
```

---

## Next Steps

- All commands → **[Command Cheatsheet](16-command-cheatsheet.md)**
- Fixing issues → **[Troubleshooting](17-troubleshooting.md)**
- Add new features → **[Extending the System](14-extending-the-system.md)**

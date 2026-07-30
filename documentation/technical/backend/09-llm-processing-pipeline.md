# LLM Processing Pipeline

How search results become curated summaries — the DeepSeek/Groq integration, anti-hallucination design, retry logic, and the empty-digest fallback.

---

## Overview

After search results are collected from Tavily, they're sent to an LLM for summarization and curation. The LLM doesn't just summarize — it selects which stories are most relevant and writes original summaries for them.

**Key design:** The LLM never sees titles or URLs. It works with positional IDs only. All factual data (headlines, links, sources) comes from the original search results. This completely eliminates hallucinated content.

```
raw_by_category                    indexed results
{repos: [{title, url,...}, ...]}  [{id:0, title, url}, {id:1,...}, ...]
       │                                  │
       ▼                                  │
_index_raw() ─── assigns IDs              │
       │                                  │
       ▼                                  │
LLM prompt (DeepSeek):                    │
  "Pick by id. Write summaries only."     │
       │                                  │
       ▼                                  │
LLM response:                             │
  [{id: 3, summary: "..."}, ...]          │
       │                                  │
       ▼                                  ▼
_resolve_picks() ──── pulls real data by id
       │
       ▼
digest: [{title: "...", summary: "...", url: "..."}, ...]
```

---

## Key Functions

### `process_results()` — The Task

```python
@task(retries=2, retry_delay_seconds=[5, 15])
def process_results(raw_by_category: dict) -> dict:
    indexed = _index_raw(raw_by_category)

    try:
        client = _build_openai_client(provider="deepseek")
        response = _call_llm(client, indexed)
        picks = _parse_response(response)
        return _resolve_picks(picks, indexed)
    except Exception as e:
        print(f"DeepSeek failed: {e}")
        try:
            client = _build_openai_client(provider="groq")
            response = _call_llm(client, indexed)
            picks = _parse_response(response)
            return _resolve_picks(picks, indexed)
        except Exception as e2:
            print(f"Groq also failed: {e2}")
            return _empty_digest(categories)
```

**Retry configuration:**
- `retries=2` — retries the entire task twice if it fails
- `retry_delay_seconds=[5, 15]` — waits 5 seconds before the first retry, 15 seconds before the second

**Provider flow:** DeepSeek (primary) → Groq (fallback) → Empty digest (last resort)

---

### `_build_openai_client()` — Provider Selection

```python
def _build_openai_client(provider: str):
    if provider == "deepseek":
        return OpenAI(
            api_key=get_secret("OPENAI_API_KEY"),
            base_url="https://api.deepseek.com",
        )
    elif provider == "groq":
        return OpenAI(
            api_key=get_secret("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1",
        )
```

**Why OpenAI SDK?** Both DeepSeek and Groq offer OpenAI-compatible APIs. Using the same client library means switching providers is a one-line change to `base_url`. The code doesn't need separate DeepSeek and Groq clients.

**Why DeepSeek as primary?**
- Cheapest per-token cost for the quality level needed
- Good at following structured JSON instructions
- Sufficient context window for all 10 categories of results

**Why Groq as fallback?**
- Free tier with generous rate limits (effectively zero cost for fallback use)
- Different infrastructure — unlikely to have simultaneous downtime with DeepSeek
- Slightly faster inference (Groq uses custom LPU hardware)

---

### `_index_raw()` — ID Assignment

```python
def _index_raw(raw_by_category: dict) -> dict:
    indexed = {}
    next_id = 0
    for category_key, results in raw_by_category.items():
        indexed[category_key] = []
        for item in results:
            indexed[category_key].append({
                "id": next_id,
                "title": item["title"],
                "url": item["url"],
                "snippet": item["snippet"],
                "source_name": item.get("source_name", ""),
                "published_date": item.get("published_date", ""),
            })
            next_id += 1
    return indexed
```

**What happens:**
1. Iterates through all categories in order
2. Assigns sequential numeric IDs (0, 1, 2, 3, ...) to every item
3. Returns a dict structured as `{category_key: [{id, title, url, snippet, ...}, ...]}`

**Example output:**
```python
{
    "repos": [
        {"id": 0, "title": "AI CLI Tool", "url": "https://...", "snippet": "A new..."},
        {"id": 1, "title": "Model Runner", "url": "https://...", "snippet": "Fast..."},
    ],
    "skills": [
        {"id": 2, "title": "Agent Skill", "url": "https://...", "snippet": "Build..."},
    ],
    ...
}
```

---

### `_build_system_prompt()` — LLM Instructions

```python
def _build_system_prompt() -> str:
    return """You are an AI news editor curating a daily digest. Your job:

For each category, select the 3-5 most significant items from the provided list.
For each selected item, write a 3-5 sentence summary that captures:
- What it is
- Why it matters
- Key details

IMPORTANT RULES:
- Return ONLY valid JSON. No markdown, no explanation.
- Use the item IDs EXACTLY as provided. Never modify IDs.
- NEVER write titles, URLs, or source names. Write ONLY summaries.
- If a category has fewer than 3 items, include all of them.
- If an item's snippet is unclear or sparse, write the best summary you can.

Response format:
{
  "repos": [{"id": 0, "summary": "..."}, {"id": 2, "summary": "..."}],
  "skills": [{"id": 5, "summary": "..."}],
  ...
}
"""
```

**Key LLM constraints:**
1. Returns JSON only — no markdown fences, no explanations before/after
2. Works with IDs — never touches actual titles/URLs
3. 3-5 most significant items per category — curation, not just summarization
4. 3-5 sentence summaries — enough detail without being verbose

---

### `_call_llm()` — The API Call

```python
def _call_llm(client, indexed: dict) -> str:
    model = "deepseek-v4-flash" if client.base_url.host == "api.deepseek.com" else "llama-3.3-70b-versatile"

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _build_system_prompt()},
            {"role": "user", "content": json.dumps(_strip_for_llm(indexed))}
        ],
        temperature=0.3,
        max_tokens=4096,
    )
    return response.choices[0].message.content
```

**`_strip_for_llm()`** sends only what the LLM needs to see:
```python
def _strip_for_llm(indexed: dict) -> list[dict]:
    # LLM only sees: category, id, snippet
    # It never sees: title, url, source_name, published_date
    stripped = []
    for cat_key, items in indexed.items():
        for item in items:
            stripped.append({
                "category": cat_key,
                "id": item["id"],
                "snippet": item["snippet"],
            })
    return stripped
```

**This is the core anti-hallucination mechanism.** The LLM receives:
```json
[
  {"category": "repos", "id": 0, "snippet": "A new open-source CLI tool for..."},
  {"category": "repos", "id": 1, "snippet": "Fast model inference runner..."},
  ...
]
```

The LLM never receives:
- `title` — it cannot hallucinate headlines
- `url` — it cannot hallucinate links
- `source_name` — it cannot attribute to wrong sources
- `published_date` — it cannot misdate stories

---

### `_parse_response()` — JSON Parsing

```python
def _parse_response(response_text: str) -> dict:
    # Try direct JSON parse
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown fences
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', response_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding JSON object boundaries
    match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from LLM response")
```

**Three levels of JSON recovery:**
1. **Direct parse** — LLM followed instructions perfectly
2. **Markdown fence extraction** — LLM wrapped JSON in ```json ... ```
3. **Regex boundary extraction** — LLM added text before/after the JSON

If all three fail, the function raises — triggering the fallback to Groq.

---

### `_resolve_picks()` — Rehydrating Real Data

```python
def _resolve_picks(llm_response: dict, indexed: dict) -> dict:
    digest = {}

    # Build id → data lookup
    id_to_data = {}
    for cat_key, items in indexed.items():
        for item in items:
            id_to_data[item["id"]] = {
                "title": item["title"],
                "url": item["url"],
                "source_name": item.get("source_name", ""),
                "published_date": item.get("published_date", ""),
            }

    # Resolve LLM picks to real data
    for cat_key, picks in llm_response.items():
        digest[cat_key] = []
        for pick in picks:
            item_id = pick["id"]
            if item_id in id_to_data:
                digest[cat_key].append({
                    "title": id_to_data[item_id]["title"],
                    "summary": pick["summary"],
                    "url": id_to_data[item_id]["url"],
                    "source_name": id_to_data[item_id]["source_name"],
                    "published_date": id_to_data[item_id]["published_date"],
                })

    return digest
```

**What happens:**
1. Builds a lookup table mapping `{id → {title, url, source, date}}`
2. For each LLM response `{category: [{id, summary}]}`, looks up the real data
3. Combines: LLM's summary + original search data (title, URL, source, date)
4. Returns the final digest

**If an ID is missing from the lookup** (unlikely but possible), the item is silently skipped.

---

### `_empty_digest()` — Last Resort

```python
def _empty_digest(categories: list[dict]) -> dict:
    digest = {}
    for cat in categories:
        digest[cat["key"]] = []
    return digest
```

If both DeepSeek and Groq fail, the digest is returned with empty arrays. The pipeline continues — email and website are still generated, but they show "no news found" for the day.

---

## Provider Fallback Flow

```
┌─────────────┐
│  Start       │
└──────┬──────┘
       ▼
┌─────────────┐     ✅ Success ──→ Return digest
│  DeepSeek    │
│  (primary)   │
└──────┬──────┘
       │ ❌ Failure (any exception)
       ▼
┌─────────────┐     ✅ Success ──→ Return digest
│  Groq        │
│  (fallback)  │
└──────┬──────┘
       │ ❌ Failure (any exception)
       ▼
┌──────────────────┐
│  _empty_digest() │ ──→ Return empty digest
│  (last resort)   │     (pipeline continues)
└──────────────────┘
```

**Failures that trigger fallback:**
- Authentication error (invalid API key)
- Rate limit exceeded
- Model unavailable or overloaded
- Network timeout
- Malformed response (JSON parsing fails after all recovery attempts)
- Any other exception from the API call

---

## Retry Behavior

`@task(retries=2, retry_delay_seconds=[5, 15])` creates this timelime:

```
Attempt 1: DeepSeek → fail (0s)
           Wait 5s
Attempt 2: Groq → fail (5s)
           Wait 15s
Attempt 3: Empty digest returned (20s)
```

If DeepSeek succeeds on attempt 1, no retries happen. The task completes (~5-10 second latency from the LLM API call).

---

## LLM Prompt Cost Optimization

The prompt is designed to minimize token usage:

1. **Snippets truncated to 500 chars** (in `search.py:_normalize()`) — prevents sending the LLM full article text
2. **ID-based selection** — the LLM returns `{id: 3}` not `{title: "...", url: "..."}`, saving output tokens
3. **3-5 items per category** — limits output to ~50 summaries max per run
4. **`temperature=0.3`** — lower creativity = more predictable output = fewer tokens wasted on divergent completions

---

## Troubleshooting

### "DeepSeek returns status 401"

Your API key is invalid or expired:
1. Check `OPENAI_API_KEY` in `.env` matches your DeepSeek dashboard
2. Verify billing is set up (DeepSeek requires it even for free tier)
3. Regenerate the key if needed

### "JSON parsing failed for both providers"

The LLM is returning non-JSON output despite explicit instructions. This is rare but handled:
1. The three-level JSON recovery usually catches wrapped/embedded JSON
2. If both providers fail, the empty digest fallback activates
3. Check the Prefect Cloud logs to see what the LLM actually returned

### "Groq returns fewer items than DeepSeek"

Different models, different behavior. Groq uses `llama-3.3-70b-versatile` which may be more conservative in selection. This is expected variance.

### "Results seem repetitive across days"

AI news coverage has natural repetition — the same big stories get covered by multiple sources on multiple days. The LLM curation helps by selecting the most significant items, but some overlap is inevitable.

---

## Next Steps

- How the digest becomes an email → **[Email Delivery](10-email-delivery.md)**
- How the digest becomes a web page → **[GitHub Pages Publishing](11-github-pages-publishing.md)**
- How error handling works → **[Resilience & Error Handling](15-resilience-and-errors.md)**

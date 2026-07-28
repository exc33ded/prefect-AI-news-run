import json
from urllib.parse import urlparse

from openai import OpenAI
from prefect import task

from daily_ai_digest.categories import CATEGORIES
from daily_ai_digest.config import get_secret

CATEGORY_LABELS = {c["key"]: c["label"] for c in CATEGORIES}

SYSTEM_PROMPT = f"""You are an editor for an AI news digest. Each category below is a \
JSON list of raw search results, each with an "id" field. For each category, dedupe \
near-identical items, rank by relevance and novelty, and select the top 4-6 items \
by "id". Return ONLY valid JSON matching this exact schema, no prose, no markdown \
fences, and do NOT invent or rewrite any id, title, or url — only choose from the \
given ids and write a 1-2 sentence summary for each:

{{"repos": [{{"id": 0, "summary": "1-2 sentence summary"}}], ...}}

The JSON must have one key per category, exactly these keys: {list(CATEGORY_LABELS.keys())}.
If a category has no usable items, return an empty list for it."""


def _empty_digest() -> dict:
    return {category: [] for category in CATEGORY_LABELS}


def _index_raw(raw_by_category: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """Assigns a stable positional id to each raw result per category, so the LLM
    can select by id instead of retyping title/url (which is how it previously
    mismatched a headline with an unrelated article's link)."""
    return {
        category: [{"id": i, **item} for i, item in enumerate(items)]
        for category, items in raw_by_category.items()
    }


def _build_user_prompt(indexed_raw: dict[str, list[dict]]) -> str:
    return json.dumps(indexed_raw, indent=2)


def _call_llm(client: OpenAI, model: str, user_prompt: str, strict: bool = False) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    if strict:
        messages.append(
            {"role": "user", "content": "Your previous response was not valid JSON. Return ONLY valid JSON, nothing else."}
        )
    response = client.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content


def _digest_from_provider(client: OpenAI, model: str, user_prompt: str) -> dict | None:
    """Runs the full call-then-JSON-retry sequence against one provider.
    Returns None only if the provider itself is unreachable/erroring (caller
    should fall back to the next provider), not on a parse failure (already
    retried once here)."""
    text = _call_llm(client, model, user_prompt)
    picks = _parse_picks(text)
    if picks is None:
        text = _call_llm(client, model, user_prompt, strict=True)
        picks = _parse_picks(text)
    return picks if picks is not None else _empty_digest()


def _parse_picks(text: str) -> dict | None:
    """Parses the LLM's {id, summary} selections. Does not resolve them against
    raw data yet - that happens in _resolve_picks so a bad/hallucinated id can
    be dropped without invalidating the whole category."""
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    picks = _empty_digest()
    for category in CATEGORY_LABELS:
        items = data.get(category, [])
        if isinstance(items, list):
            picks[category] = items[:6]
    return picks


def _source_name(url: str) -> str:
    host = urlparse(url).netloc.removeprefix("www.")
    return host.split(".")[0].upper() if host else "SOURCE"


def _resolve_picks(picks: dict, indexed_raw: dict[str, list[dict]]) -> dict:
    """Turns {id, summary} picks into full digest items by pulling title/url
    straight from our own indexed raw data - the LLM never writes those fields,
    so it can't mismatch a headline with the wrong article's link."""
    digest = _empty_digest()
    for category, category_picks in picks.items():
        by_id = {r["id"]: r for r in indexed_raw.get(category, [])}
        items = []
        for pick in category_picks:
            if not isinstance(pick, dict):
                continue
            raw = by_id.get(pick.get("id"))
            if raw is None:
                continue
            items.append(
                {
                    "title": raw.get("title", ""),
                    "summary": pick.get("summary", ""),
                    "url": raw.get("url", ""),
                    "source_name": _source_name(raw.get("url", "")),
                    "published_date": raw.get("published_date"),
                }
            )
        digest[category] = items
    return digest


@task(retries=2, retry_delay_seconds=[5, 15])
def process_results(raw_by_category: dict[str, list[dict]]) -> dict:
    indexed_raw = _index_raw(raw_by_category)
    user_prompt = _build_user_prompt(indexed_raw)

    try:
        client = OpenAI(api_key=get_secret("OPENAI_API_KEY"), base_url="https://api.deepseek.com")
        picks = _digest_from_provider(client, "deepseek-v4-flash", user_prompt)
    except Exception:
        try:
            groq_client = OpenAI(api_key=get_secret("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")
            picks = _digest_from_provider(groq_client, "llama-3.3-70b-versatile", user_prompt)
        except Exception:
            picks = _empty_digest()

    return _resolve_picks(picks, indexed_raw)

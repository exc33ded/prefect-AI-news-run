import json

from openai import OpenAI
from prefect import task

from daily_ai_digest.categories import CATEGORIES
from daily_ai_digest.config import get_secret

CATEGORY_LABELS = {c["key"]: c["label"] for c in CATEGORIES}

SYSTEM_PROMPT = f"""You are an editor for an AI news digest. For each category of raw \
search results, dedupe near-identical items, rank by relevance and novelty, and select \
the top 4-6 items. Return ONLY valid JSON matching this exact schema, no prose, no \
markdown fences:

{{"repos": [{{"title": "...", "summary": "1-2 sentence summary", "url": "...", "source_name": "..."}}], ...}}

The JSON must have one key per category, exactly these keys: {list(CATEGORY_LABELS.keys())}.
If a category has no usable items, return an empty list for it."""


def _empty_digest() -> dict:
    return {category: [] for category in CATEGORY_LABELS}


def _build_user_prompt(raw_by_category: dict[str, list[dict]]) -> str:
    return json.dumps(raw_by_category, indent=2)


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
    digest = _parse_digest(text)
    if digest is None:
        text = _call_llm(client, model, user_prompt, strict=True)
        digest = _parse_digest(text)
    return digest if digest is not None else _empty_digest()


def _parse_digest(text: str) -> dict | None:
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    digest = _empty_digest()
    for category in CATEGORY_LABELS:
        items = data.get(category, [])
        if isinstance(items, list):
            digest[category] = items[:6]
    return digest


def _attach_published_dates(digest: dict, raw_by_category: dict[str, list[dict]]) -> dict:
    """The LLM doesn't reliably echo published_date, so join it back from the raw
    search results by url instead of trusting the model's output for it."""
    for category, items in digest.items():
        url_to_date = {r["url"]: r.get("published_date") for r in raw_by_category.get(category, [])}
        for item in items:
            item["published_date"] = url_to_date.get(item.get("url"))
    return digest


@task(retries=2, retry_delay_seconds=[5, 15])
def process_results(raw_by_category: dict[str, list[dict]]) -> dict:
    user_prompt = _build_user_prompt(raw_by_category)

    try:
        client = OpenAI(api_key=get_secret("OPENAI_API_KEY"), base_url="https://api.deepseek.com")
        digest = _digest_from_provider(client, "deepseek-v4-flash", user_prompt)
    except Exception:
        try:
            groq_client = OpenAI(api_key=get_secret("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")
            digest = _digest_from_provider(groq_client, "llama-3.3-70b-versatile", user_prompt)
        except Exception:
            digest = _empty_digest()

    return _attach_published_dates(digest, raw_by_category)

from prefect import task
from tavily import TavilyClient

from daily_ai_digest.categories import CATEGORIES
from daily_ai_digest.config import get_secret


def _tavily_keys() -> list[str]:
    keys = []
    for i in range(1, 11):
        try:
            keys.append(get_secret(f"TAVILY_API_KEY_{i}"))
        except Exception:
            pass
    return keys


def _search_with_fallback(query: str, **kwargs) -> dict:
    """Always tries keys in order (key 1 first); only moves to the next key
    if the current one fails, rather than distributing load round-robin."""
    keys = _tavily_keys()
    if not keys:
        return {"results": []}

    last_error = None
    for key in keys:
        try:
            client = TavilyClient(api_key=key)
            return client.search(query, **kwargs)
        except Exception as e:
            last_error = e
            continue
    raise last_error


def _normalize(raw: dict) -> list[dict]:
    items = []
    for r in raw.get("results", []):
        items.append(
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", ""),
                "published_date": r.get("published_date"),
            }
        )
    return items


@task
def search_category(query: str) -> list[dict]:
    try:
        raw = _search_with_fallback(query, time_range="day", max_results=10)
        return _normalize(raw)
    except Exception:
        return []


def submit_all_searches() -> dict:
    """Submits one search_category task per entry in CATEGORIES, keyed by category key."""
    return {category["key"]: search_category.submit(category["query"]) for category in CATEGORIES}

from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from prefect import task
from tavily import TavilyClient

from daily_ai_digest.categories import CATEGORIES
from daily_ai_digest.config import get_secret

REPO_MAX_AGE_DAYS = 90


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


def _github_repo_age_days(url: str) -> int | None:
    """Days since the repo at `url` was created, or None if `url` isn't a
    github.com/<owner>/<repo> URL or the lookup fails (fail open - caller
    keeps the item rather than dropping it on an inconclusive result)."""
    parts = urlparse(url).path.strip("/").split("/")
    if urlparse(url).netloc.removeprefix("www.") != "github.com" or len(parts) < 2:
        return None
    owner, repo = parts[0], parts[1]
    try:
        token = get_secret("GITHUB_TOKEN")
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        response = httpx.get(f"https://api.github.com/repos/{owner}/{repo}", headers=headers, timeout=10)
        response.raise_for_status()
        created_at = datetime.strptime(response.json()["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - created_at).days
    except Exception:
        return None


def _filter_stale_repos(items: list[dict], max_age_days: int = REPO_MAX_AGE_DAYS) -> list[dict]:
    """Drops items whose GitHub repo is confirmed older than max_age_days.
    Keeps items whose age can't be determined (non-GitHub URL, API error)."""
    kept = []
    for item in items:
        age_days = _github_repo_age_days(item.get("url", ""))
        if age_days is not None and age_days > max_age_days:
            continue
        kept.append(item)
    return kept


@task
def search_category(query: str, category: str = "") -> list[dict]:
    try:
        raw = _search_with_fallback(query, time_range="day", max_results=10)
        items = _normalize(raw)
        if category == "repos":
            items = _filter_stale_repos(items)
        return items
    except Exception:
        return []


def submit_all_searches() -> dict:
    """Submits one search_category task per entry in CATEGORIES, keyed by category key."""
    return {
        category["key"]: search_category.submit(category["query"], category=category["key"])
        for category in CATEGORIES
    }

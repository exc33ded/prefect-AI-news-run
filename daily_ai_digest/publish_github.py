import base64
import json
from pathlib import Path

import httpx
from jinja2 import Environment, FileSystemLoader
from prefect import task

from daily_ai_digest.config import get_secret


def _tojson_safe(value) -> str:
    """json.dumps, with </script> escaped so a headline scraped from an attacker's
    page can't break out of the embedded <script type="application/json"> block."""
    return json.dumps(value).replace("</", "<\\/")


_TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(_TEMPLATES_DIR))
_env.filters["tojson"] = _tojson_safe


def _get_file(repo: str, token: str, path: str, headers: dict) -> str | None:
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    response = httpx.get(url, headers=headers)
    if response.status_code != 200:
        return None
    return base64.b64decode(response.json()["content"]).decode("utf-8")


def _put_file(repo: str, token: str, path: str, content: str, message: str) -> None:
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    existing = httpx.get(url, headers=headers)
    sha = existing.json().get("sha") if existing.status_code == 200 else None

    body = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
    }
    if sha:
        body["sha"] = sha

    response = httpx.put(url, headers=headers, json=body, timeout=30)
    response.raise_for_status()


@task
def fetch_archive_editions() -> list[dict]:
    """Reads docs/archive.json (empty list if it doesn't exist yet). Called before
    rendering so the masthead's Vol./No. can be computed from real publish history."""
    repo = get_secret("GITHUB_REPO")
    token = get_secret("GITHUB_TOKEN")
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    raw = _get_file(repo, token, "docs/archive.json", headers)
    return json.loads(raw) if raw else []


def _update_archive(repo: str, token: str, editions: list[dict], meta: dict) -> None:
    """Keeps docs/archive.json as the list of every published edition, and
    re-renders docs/archive.html from it so past editions stay browsable."""
    editions = [e for e in editions if e["iso_date"] != meta["iso_date"]]
    editions.append(meta)
    editions.sort(key=lambda e: e["iso_date"], reverse=True)

    _put_file(repo, token, "docs/archive.json", json.dumps(editions, indent=2), f"Update archive index {meta['iso_date']}")

    archive_html = _env.get_template("archive.html").render(total=len(editions), editions=editions)
    _put_file(repo, token, "docs/archive.html", archive_html, f"Update archive page {meta['iso_date']}")


@task
def publish_page(html: str, editions: list[dict], meta: dict) -> None:
    repo = get_secret("GITHUB_REPO")
    token = get_secret("GITHUB_TOKEN")
    iso_date = meta["iso_date"]

    _put_file(repo, token, "docs/index.html", html, f"Publish AI digest {iso_date}")
    _put_file(repo, token, f"docs/{iso_date}.html", html, f"Archive AI digest {iso_date}")
    _update_archive(repo, token, editions, meta)

import base64

import httpx
from prefect import task

from daily_ai_digest.config import get_secret


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
def publish_page(html: str, iso_date: str) -> None:
    repo = get_secret("GITHUB_REPO")
    token = get_secret("GITHUB_TOKEN")

    _put_file(repo, token, "docs/index.html", html, f"Publish AI digest {iso_date}")
    _put_file(repo, token, f"docs/{iso_date}.html", html, f"Archive AI digest {iso_date}")

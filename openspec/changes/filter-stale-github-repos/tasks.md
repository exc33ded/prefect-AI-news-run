## 1. Implement the freshness filter

- [x] 1.1 In `daily_ai_digest/search.py`, add `_github_repo_age_days(url: str) -> int | None` that parses `owner/repo` from a `github.com` URL, calls `GET https://api.github.com/repos/{owner}/{repo}` with the `GITHUB_TOKEN` secret, and returns days since `created_at` (or `None` if the URL isn't a GitHub repo URL or the call fails).
- [x] 1.2 Add `_filter_stale_repos(items: list[dict], max_age_days: int = 90) -> list[dict]` that drops items where `_github_repo_age_days(item["url"])` returns a value `> max_age_days`, keeping items where it returns `None` or a value `<= max_age_days`.
- [x] 1.3 Call `_filter_stale_repos` on the normalized results only for the `repos` category inside `search_category` (or `submit_all_searches`), leaving all other categories untouched.

## 2. Tests

- [x] 2.1 Add unit tests (mocking the GitHub API call) covering: repo older than 90 days is dropped, repo within 90 days is kept, non-GitHub URL is kept unfiltered, API error is kept unfiltered (fail open), non-`repos` categories are never filtered.
- [x] 2.2 Run `uv run python test_flow.py` (or the project's test runner) to confirm existing checks still pass alongside the new ones.

## 3. Verification

- [x] 3.1 Run `main.py` (or a scoped script) against real search results for the `repos` category and confirm `different-ai/openwork` (or any repo older than 90 days) is excluded from the raw results passed to `process_results`.
- [x] 3.2 Confirm the next published edition's "Trending AI GitHub Repos" section only contains repos created within the last 90 days.

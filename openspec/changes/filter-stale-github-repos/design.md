## Context

`search_category` (daily_ai_digest/search.py) runs Tavily search per category and hands raw `{title, url, snippet, published_date}` results straight to `process_results` (process.py), which asks an LLM to rank/pick items. For the `repos` category, "published_date" from Tavily reflects when the page/article was indexed, not when the GitHub repo was created — a months-old repo with a fresh blog post or listicle mention still looks "new" to the search and to the LLM. The only reliable freshness signal is the repo's actual `created_at` from the GitHub API, which nothing currently fetches.

## Goals / Non-Goals

**Goals:**
- Before the `repos` category's raw results reach `process_results`, drop any item whose GitHub repo `created_at` is older than a fixed threshold.
- Reuse the existing `get_secret("GITHUB_TOKEN")` (already used in publish_github.py) to authenticate GitHub API calls and avoid the 60/hr unauthenticated rate limit.
- Fail open: if the GitHub API lookup fails (network error, rate limit, non-repo URL) for a given item, keep the item rather than dropping it — the filter should only ever remove items it can positively confirm are stale.

**Non-Goals:**
- No change to the 9 non-`repos` categories.
- No change to the LLM prompt, digest schema, or ranking logic — this is a pre-filter on raw candidates, not a ranking signal handed to the LLM.
- No persistent cache/database of previously-seen repos — a stateless per-run API lookup is enough at this scale (up to 10 repo URLs/day).

## Decisions

- **Filter at the raw-results stage, in `search.py`, not inside `process.py`**: add a `_filter_stale_repos(items: list[dict]) -> list[dict]` function called only for the `repos` category's results in `submit_all_searches`/`search_category`, before they're returned. Keeps `process_results` category-agnostic (it doesn't know or care which category is `repos`), matching the existing pattern where `search.py` owns per-source normalization and `process.py` owns generic ranking.
- **Threshold: 90 days, as a module constant**: chosen because "new open-source AI project launch" style news typically stays relevant for a few months after launch (e.g. a v1.0 announcement, HN front-page mention); a hard 90-day cutoff is simple and avoids needing per-repo judgment calls. Alternative considered: scaling the threshold by star velocity — rejected as speculative complexity (YAGNI) for a once-a-day digest of ~10 repo candidates.
- **GitHub API call: `GET /repos/{owner}/{repo}`, read `created_at`**: same REST API already used in publish_github.py, so no new dependency. Parse `owner/repo` out of the item's `url` via `urlparse`; if the URL doesn't match `github.com/<owner>/<repo>` shape, skip the filter for that item (fail open, per Goals).
- **No new secret**: reuse `GITHUB_TOKEN` already configured for `publish_github.py`. It already has read scope on the target repo; GitHub API read access to *other* public repos works with any valid PAT regardless of which repo it was scoped for, since the contents/repos read endpoint is public-data.

## Risks / Trade-offs

- [GitHub API rate limit (5000/hr authenticated) exhausted by other usage] → Mitigation: at most 10 lookups/day (one per repo candidate before LLM picks top 4-6), negligible against the limit; failures fail open rather than raising.
- [90-day threshold is a blunt heuristic — a repo that relaunches under a new name/major rewrite after 90 days won't be flagged as "new"] → Accepted trade-off, out of scope; call it out as a follow-up if it becomes a recurring complaint.
- [Extra per-run latency from up to 10 sequential GitHub API calls] → Mitigation: calls are simple GETs (fast), and search already runs in parallel via `.submit()`; this filter only affects the `repos` category's task, not overall flow critical path meaningfully.

## Migration Plan

No data migration. Deploy is: merge the change, next scheduled flow run applies the filter automatically to the `repos` category. Rollback is a plain revert of the touched file(s).

## Open Questions

- Should the 90-day threshold be configurable via env var instead of a hardcoded constant? Defaulting to hardcoded for now (YAGNI) — revisit if the user wants to tune it without a code change.

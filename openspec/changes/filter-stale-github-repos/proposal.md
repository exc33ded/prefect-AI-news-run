## Why

Today's "Trending AI GitHub Repos" top story was `different-ai/openwork` — a repo created 2026-01-14 (~6.5 months old) already sitting at 17.4k stars. The `repos` category's search query asks for "new open-source AI project launch announcement," but nothing in the pipeline actually checks a repo's age before it's selected, so an established, already-popular repo can resurface in search results and get picked as if it were breaking news. The digest should only feature repos that are genuinely new (or newly trending), not repos that happen to match the query text months after launch.

## What Changes

- Add a GitHub repo age/freshness check to the `repos` category's pipeline: given a candidate item's URL, look up the repo's `created_at` via the GitHub API and drop candidates older than a configurable threshold (e.g. 60-90 days) before they reach the LLM ranking step.
- Items whose URL isn't a GitHub repo (or where the lookup fails) are left untouched — the filter only removes items it can positively confirm are stale, never sight-unseen.
- No change to the other 9 categories' pipelines.

## Capabilities

### New Capabilities
- `github-repo-freshness`: filters stale (already-established) GitHub repos out of the "Trending AI GitHub Repos" category before LLM selection, based on the repo's actual creation date.

### Modified Capabilities
(none — no existing `openspec/specs/` entries for this project; `daily-digest-generation`'s delta spec from the prior change has not yet been archived into `openspec/specs/`)

## Impact

- `daily_ai_digest/search.py` — new step (or new module) to enrich/filter `repos` category results with GitHub repo age before they're handed to `process_results`.
- `daily_ai_digest/config.py` — may need a `GITHUB_TOKEN`-authenticated GitHub API call (already used elsewhere for publishing) to avoid unauthenticated rate limits.
- No change to `process.py`'s prompt/schema or to the digest item shape.

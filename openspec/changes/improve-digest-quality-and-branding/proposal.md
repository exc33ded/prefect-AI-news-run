## Why

Three separate problems are hurting the daily digest's quality and reliability today: (1) the LLM-written summaries are too short (1-2 sentences) to be genuinely useful, (2) the email template still says "THE AI DAILY" while the site, archive, and every other surface say "The AI Herald," so subscribers see a different publication name in their inbox than on the page they click through to, and (3) a real reliability bug in the Tavily fallback means a transient error (timeout, 5xx) on the first API key aborts the whole search instead of trying the remaining 9 keys.

## What Changes

- Rewrite `SYSTEM_PROMPT` in `process.py` to ask for a longer, more substantive per-item summary (roughly 3-5 sentences covering what happened, why it matters, and any concrete detail/number), and raise the model's completion budget accordingly.
- Replace every hardcoded "THE AI DAILY" / "The AI Daily" string in `daily_ai_digest/templates/email.html` with "The AI Herald" to match the page, archive, and masthead branding.
- **BREAKING** (internal only): broaden the except clause in `search.py::_search_with_fallback` so any exception from one Tavily key falls through to the next key, not just `UsageLimitExceededError`/`InvalidAPIKeyError`. Changes fallback behavior but no public interface.

## Capabilities

### New Capabilities
- `daily-digest-generation`: captures the three behavior requirements below (substantive summaries, consistent email branding, resilient search fallback) since no spec previously existed for this project's digest pipeline.

### Modified Capabilities
(none — no prior `openspec/specs/` entries exist for this project)

## Impact

- `daily_ai_digest/process.py` — `SYSTEM_PROMPT`, `_call_llm` (token budget)
- `daily_ai_digest/templates/email.html` — title, masthead, footer text
- `daily_ai_digest/search.py` — `_search_with_fallback` exception handling
- No API/schema changes; digest item shape (`title`, `summary`, `url`, `source_name`, `published_date`) is unchanged, only `summary` gets longer.

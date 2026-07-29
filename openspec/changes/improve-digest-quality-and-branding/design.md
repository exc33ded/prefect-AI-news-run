## Context

`process_results` (daily_ai_digest/process.py) sends all raw search results to DeepSeek (falling back to Groq/Llama on error), asking for 4-6 picks per category with a 1-2 sentence summary each. Output is thin — closer to a headline restatement than a useful digest. The email template (daily_ai_digest/templates/email.html) was branded "THE AI DAILY" before the publication was renamed "The AI Herald" everywhere else (page templates, archive, masthead); the rename never touched the email. Separately, `_search_with_fallback` in search.py only advances to the next Tavily key on `UsageLimitExceededError`/`InvalidAPIKeyError` — any other exception (timeout, connection error, 500) propagates immediately, defeating the 10-key fallback pool for exactly the failure mode it exists to handle.

## Goals / Non-Goals

**Goals:**
- Longer, substantive per-item summaries (~3-5 sentences: what happened, why it matters, one concrete detail/number) without changing the digest item schema.
- Email branding matches the rest of the publication ("The AI Herald") in title, masthead, and footer.
- Any transient per-key failure in Tavily search falls through to the next key, not just quota/auth errors.

**Non-Goals:**
- No change to which categories exist, how many items are picked per category, or the JSON schema (`{id, summary}` picks, resolved digest item shape).
- No new LLM provider, no change to the DeepSeek→Groq fallback order.
- No redesign of the email/page visual layout — copy changes only for branding.

## Decisions

- **Prompt change, not schema change**: extend `SYSTEM_PROMPT`'s summary instruction from "1-2 sentence summary" to "3-5 sentence summary covering what happened, why it matters, and one concrete detail or number." Keep the `{"id":..., "summary":...}` shape untouched so `_resolve_picks` needs no changes. Alternative considered: adding a separate "detail" field — rejected, adds schema/template complexity for no real benefit over one richer prose field.
- **No explicit max_tokens bump unless truncation is observed**: OpenAI-compatible chat completions default to generous limits for both DeepSeek and Groq's llama-3.3-70b; a 5x longer summary across ~40-60 items total is well within default budgets. Skip pre-emptive token-limit tuning (YAGNI) — call it out as a follow-up if truncation shows up in practice.
- **Global find/replace for branding**: replace all "AI DAILY"/"AI Daily" occurrences in `email.html` (title tag, masthead div, footer div) with "The AI Herald" / "THE AI HERALD" matching each spot's existing case convention. No templating variable introduced (e.g. a `site_name` context var) since the name is a hardcoded string everywhere else too (page templates) — introducing a variable only here would be inconsistent, not simpler.
- **Broaden the except in `_search_with_fallback`**: catch bare `Exception` per key instead of the two named ones, keep `last_error` re-raise after the loop exhausts all keys. This is the minimal fix — one line — versus building a retry/backoff layer, which isn't needed since the loop itself already tries up to 10 keys.

## Risks / Trade-offs

- [Longer summaries increase LLM cost/latency per run] → Bounded: same number of items (24-60 across 10 categories), summary length increase is the only cost driver; acceptable for a once-daily batch job.
- [Broadening except in search fallback could mask a systematic bug across all 10 keys] → Mitigation: `last_error` is still re-raised after all keys are exhausted, and the outer `search_category` task already catches everything and returns `[]`, logged via existing category-level warning in flow.py.
- [Rebranding email footer/title is purely cosmetic and easy to miss a spot] → Mitigation: grep for "AI Daily"/"AI DAILY" case-insensitively after the edit to confirm no stray occurrence remains.

## Migration Plan

No data migration. Deploy is: merge the three file changes, next scheduled Prefect flow run picks up the new prompt/template/fallback behavior automatically. Rollback is a plain revert of the three files.

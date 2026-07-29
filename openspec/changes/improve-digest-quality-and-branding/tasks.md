## 1. Richer AI summaries

- [x] 1.1 Update `SYSTEM_PROMPT` in `daily_ai_digest/process.py` to request a 3-5 sentence summary per item (what happened, why it matters, one concrete detail/number) instead of "1-2 sentence summary," keeping the `{"id": 0, "summary": "..."}` schema unchanged.
- [x] 1.2 Run `process_results` against a sample/real `raw_by_category` payload (e.g. via `test_flow.py` or a manual script) and confirm returned summaries are visibly longer and still valid JSON parsed by `_parse_picks`.

## 2. Fix email branding mismatch

- [x] 2.1 Replace `<title>THE AI DAILY — {{ date }}</title>` in `daily_ai_digest/templates/email.html` with `<title>The AI Herald — {{ date }}</title>`.
- [x] 2.2 Replace the masthead `THE AI DAILY` div text with `THE AI HERALD` (or `The AI Herald`, matching the casing style already used in `edition.html`'s masthead).
- [x] 2.3 Replace the footer `THE AI DAILY • An automated digest` text with `THE AI HERALD • An automated digest`.
- [x] 2.4 Grep `daily_ai_digest/templates/email.html` for `-i "ai daily"` to confirm no remaining occurrence.

## 3. Harden Tavily search fallback

- [x] 3.1 In `daily_ai_digest/search.py::_search_with_fallback`, broaden the `except (UsageLimitExceededError, InvalidAPIKeyError)` clause to `except Exception`, keeping `last_error = e; continue` so any per-key failure advances to the next key.
- [x] 3.2 Verify `search_category`'s outer try/except still returns `[]` on total exhaustion (no behavior change needed there, just confirm).

## 4. Verification

- [x] 4.1 Run the existing test/flow entry point (`test_flow.py` or `main.py`) end-to-end against real or mocked APIs to confirm the flow still completes and produces an email + page with the new summary length and correct branding.
- [x] 4.2 Visually check the rendered email HTML (open in browser) to confirm "The AI Herald" appears in title/masthead/footer and summaries read as multi-sentence paragraphs.

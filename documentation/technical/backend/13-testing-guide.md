# Testing Guide

The project's test suite — 15 self-test functions covering search, processing, formatting, and publishing logic. How to run them, what they test, and how to add more.

---

## Running Tests

```bash
uv run python test_flow.py
```

**No API keys needed.** The tests are self-contained — they use mock data and test pure functions, not network calls.

**Expected output:**

```
test_search_normalize ... OK
test_filter_stale_repos ... OK
test_github_repo_age ... OK
test_process_results_empty ... OK
test_index_raw ... OK
test_resolve_picks ... OK
test_empty_digest ... OK
test_to_roman ... OK
test_volume_and_issue ... OK
test_render_email ... OK
test_render_page ... OK
test_fetch_archive_editions ... OK
test_put_file ... OK
test_update_archive ... OK
test_daily_ai_digest_smoke ... OK

All 15 tests passed!
```

---

## Test Structure

The test file uses a simple pattern — no pytest, no unittest, just functions:

```python
def test_something():
    result = function_under_test(input)
    assert result == expected, f"Expected {expected}, got {result}"
    print("OK")
```

**Why no pytest?** The project doesn't need a test framework. 15 simple assertions with print-based reporting is sufficient for a pipeline this size. No test dependencies = no additional complexity.

---

## Test Inventory

### Search Tests

| Test | What It Verifies |
|------|-----------------|
| `test_search_normalize()` | Raw Tavily results are correctly transformed into the standard `{title, url, snippet, published_date, source_name}` format |
| `test_filter_stale_repos()` | Repos older than 90 days are removed; non-GitHub URLs pass through; failed age lookups pass through (fail-open) |
| `test_github_repo_age()` | `_github_repo_age_days()` correctly extracts owner/repo from GitHub URLs and calculates age; non-GitHub URLs return None |

### Processing Tests

| Test | What It Verifies |
|------|-----------------|
| `test_process_results_empty()` | If both LLM providers fail, `_empty_digest()` returns a dict with all category keys but empty result arrays |
| `test_index_raw()` | `_index_raw()` assigns sequential IDs to results across categories |
| `test_resolve_picks()` | LLM picks (by ID) are correctly resolved back to titles, URLs, and sources from the raw search data |
| `test_empty_digest()` | `_empty_digest()` returns the correct structure with all category keys |

### Formatting Tests

| Test | What It Verifies |
|------|-----------------|
| `test_to_roman()` | Roman numeral conversion: 1→I, 4→IV, 9→IX, 49→XLIX, 2026→MMXXVI |
| `test_volume_and_issue()` | Volume/Issue calculation: first run = Vol I, No 1; mid-month = correct sequential numbering |
| `test_render_email()` | Email template renders without Jinja2 errors; contains expected content (masthead, category sections, CTA) |
| `test_render_page()` | Web page template renders without Jinja2 errors; contains lead story, sections, volume/issue numbers |

### Publishing Tests

| Test | What It Verifies |
|------|-----------------|
| `test_fetch_archive_editions()` | Simulated archive.json fetch returns valid editions list |
| `test_put_file()` | `_put_file()` correctly encodes content as base64 and formats the GitHub API request body |
| `test_update_archive()` | Archive update correctly appends a new edition and calls render/put for archive files |

### Integration Test

| Test | What It Verifies |
|------|-----------------|
| `test_daily_ai_digest_smoke()` | The full flow runs end-to-end with mock data; no exceptions; all stages complete |

---

## Adding a New Test

Follow the existing pattern:

```python
def test_your_new_test():
    """Test that [something] works correctly."""
    # Setup
    input_data = {...}

    # Execute
    result = your_function(input_data)

    # Assert
    assert result == expected_output, f"Got: {result}"
    print("test_your_new_test ... OK")
```

**Then add it to the main block:**

```python
if __name__ == "__main__":
    tests = [
        test_search_normalize,
        test_filter_stale_repos,
        # ... existing tests ...
        test_your_new_test,  # ← Add here
    ]
    ...
```

---

## Test Design Principles

### 1. No Network

Tests never call external APIs. Mock data simulates Tavily search results, LLM responses, and GitHub API calls. This makes tests:
- Fast (all 15 run in <2 seconds)
- Reliable (no flakyness from network issues)
- Free (no API costs from test runs)

### 2. Pure Functions

Most tests exercise pure functions — same input always produces same output. The functions that do I/O (API calls, file reads) are mocked or tested separately.

### 3. Fail-First Assertions

Each test has explicit assertions with failure messages:

```python
assert result == expected, f"Expected {expected}, got {result}"
```

This makes test failures self-documenting — the error message tells you exactly what went wrong.

### 4. No Test Dependencies

Tests are independent. You can run any single test in isolation. No shared state between tests.

---

## Test Coverage Areas

| Area | Covered? | Notes |
|------|----------|-------|
| Search normalization | ✅ | Tests map raw API → standard format |
| Stale repo filtering | ✅ | Tests 90-day threshold, edge cases |
| LLM pick resolution | ✅ | Tests ID-based resolution |
| Empty digest fallback | ✅ | Tests when both providers fail |
| Volume/Issue numbering | ✅ | Tests Roman numerals, sequential counting |
| Template rendering | ✅ | Tests Jinja2 compiles and renders |
| Email delivery (Resend) | ❌ | Requires network; tested manually |
| GitHub publishing (API) | ❌ | Requires network; tested manually |
| Tavily search (API) | ❌ | Requires API key; tested via local runs |
| DeepSeek/Groq (API) | ❌ | Requires API keys; tested via local runs |
| Prefect deployment | ❌ | Tested by manual deployment + run |

---

## Pre-Commit Testing Workflow

Before committing changes:

```bash
# 1. Run tests
uv run python test_flow.py

# 2. Run the full pipeline locally (requires API keys)
uv run python main.py

# 3. If everything passes
git add .
git commit -m "Your changes"
git push
```

---

## Debugging Failed Tests

### Template Rendering Errors

```
test_render_email ... FAIL: 'NoneType' object has no attribute 'render'
```

The Jinja2 template can't find a variable. Check that all template variables are passed in `format_email.py`.

### Volume/Issue Errors

```
test_volume_and_issue ... FAIL: Expected ('II', 1), got ('I', 1)
```

The date/edition calculation is likely off. Check `_volume_and_issue()` logic — especially the `months_diff` formula and the issue counting.

### ID Resolution Errors

```
test_resolve_picks ... FAIL: KeyError 'title'
```

The LLM returned an ID that doesn't exist in the indexed data. Check that `_index_raw()` assigns IDs correctly and `_resolve_picks()` uses the same ID scheme.

---

## Next Steps

- Adding new features → **[Extending the System](14-extending-the-system.md)**
- Error handling patterns → **[Resilience & Error Handling](15-resilience-and-errors.md)**
- Fixing issues → **[Troubleshooting](17-troubleshooting.md)**

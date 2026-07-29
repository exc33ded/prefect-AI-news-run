"""Self-check for digest-processing fallback and search empty-tolerance logic.
No network calls — mocks the DeepSeek/Tavily boundaries. Run: uv run python test_flow.py
"""
from unittest.mock import MagicMock, patch

from daily_ai_digest.categories import CATEGORIES
from daily_ai_digest.process import (
    CATEGORY_LABELS,
    _empty_digest,
    _index_raw,
    _parse_picks,
    _resolve_picks,
    _source_name,
    process_results,
)
from daily_ai_digest.search import _filter_stale_repos, _normalize


def test_parse_picks_valid():
    text = '{"repos": [{"id": 0, "summary": "s"}], "skills": [], "prompting": [], "papers": []}'
    picks = _parse_picks(text)
    assert picks is not None
    assert len(picks["repos"]) == 1
    assert picks["skills"] == []


def test_parse_picks_malformed_returns_none():
    assert _parse_picks("not json") is None


def test_index_raw_assigns_positional_ids():
    raw = {"repos": [{"title": "a", "url": "u1"}, {"title": "b", "url": "u2"}]}
    indexed = _index_raw(raw)
    assert indexed["repos"][0]["id"] == 0
    assert indexed["repos"][1]["id"] == 1


def test_source_name_derives_from_domain():
    assert _source_name("https://www.github.com/foo/bar") == "GITHUB"
    assert _source_name("https://arxiv.org/abs/123") == "ARXIV"
    assert _source_name("") == "SOURCE"


def test_resolve_picks_pulls_title_url_from_raw_not_llm():
    indexed_raw = _index_raw({"repos": [{"title": "Real Headline", "url": "https://real.example/a", "published_date": "2026-07-28"}]})
    picks = {"repos": [{"id": 0, "summary": "AI-written summary"}]}
    digest = _resolve_picks(picks, indexed_raw)
    assert len(digest["repos"]) == 1
    item = digest["repos"][0]
    assert item["title"] == "Real Headline"
    assert item["url"] == "https://real.example/a"
    assert item["summary"] == "AI-written summary"
    assert item["source_name"] == "REAL"
    assert item["published_date"] == "2026-07-28"


def test_resolve_picks_drops_hallucinated_id():
    indexed_raw = _index_raw({"repos": [{"title": "a", "url": "u1"}]})
    picks = {"repos": [{"id": 0, "summary": "s"}, {"id": 5, "summary": "hallucinated"}]}
    digest = _resolve_picks(picks, indexed_raw)
    assert len(digest["repos"]) == 1


def test_process_results_falls_back_on_bad_then_good_json():
    bad = MagicMock()
    bad.choices = [MagicMock(message=MagicMock(content="not json"))]
    good = MagicMock()
    good.choices = [MagicMock(message=MagicMock(content='{"repos": []}'))]

    with patch("daily_ai_digest.process.get_secret", return_value="fake-key"), \
         patch("daily_ai_digest.process.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.side_effect = [bad, good]
        digest = process_results.fn({"repos": []})
        assert digest == _empty_digest()


def test_process_results_all_fallbacks_fail_returns_empty_digest():
    bad = MagicMock()
    bad.choices = [MagicMock(message=MagicMock(content="still not json"))]

    with patch("daily_ai_digest.process.get_secret", return_value="fake-key"), \
         patch("daily_ai_digest.process.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.side_effect = [bad, bad]
        digest = process_results.fn({"repos": []})
        assert digest == _empty_digest()


def test_process_results_falls_back_to_groq_when_deepseek_errors():
    good = MagicMock()
    good.choices = [MagicMock(message=MagicMock(content='{"repos": [{"id": 0, "summary": "s"}]}'))]

    with patch("daily_ai_digest.process.get_secret", return_value="fake-key"), \
         patch("daily_ai_digest.process.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.side_effect = [Exception("deepseek down"), good]
        digest = process_results.fn({"repos": [{"url": "https://real.example/a", "title": "t", "snippet": "", "published_date": None}]})
        assert len(digest["repos"]) == 1
        assert digest["repos"][0]["title"] == "t"


def test_process_results_empty_digest_when_both_providers_fail():
    with patch("daily_ai_digest.process.get_secret", return_value="fake-key"), \
         patch("daily_ai_digest.process.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.side_effect = Exception("down")
        digest = process_results.fn({"repos": []})
        assert digest == _empty_digest()


def test_process_results_cannot_mismatch_title_and_url():
    """Regression test for the bug where DeepSeek attached a real-but-wrong
    url to a different headline. Since the LLM now only selects by id and
    writes a summary, title/url always come from the same raw record."""
    good = MagicMock()
    good.choices = [MagicMock(message=MagicMock(content='{"repos": [{"id": 1, "summary": "s"}]}'))]

    with patch("daily_ai_digest.process.get_secret", return_value="fake-key"), \
         patch("daily_ai_digest.process.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.side_effect = [good]
        raw_by_category = {
            "repos": [
                {"url": "https://a.example/one", "title": "Story One", "snippet": "", "published_date": None},
                {"url": "https://b.example/two", "title": "Story Two", "snippet": "", "published_date": None},
            ]
        }
        digest = process_results.fn(raw_by_category)
        assert digest["repos"][0]["title"] == "Story Two"
        assert digest["repos"][0]["url"] == "https://b.example/two"


def test_search_normalize_handles_empty_results():
    assert _normalize({"results": []}) == []
    assert _normalize({}) == []


def test_search_normalize_maps_fields():
    raw = {"results": [{"title": "T", "url": "U", "content": "C", "published_date": "2026-01-01"}]}
    items = _normalize(raw)
    assert items == [{"title": "T", "url": "U", "snippet": "C", "published_date": "2026-01-01"}]


def test_filter_stale_repos_drops_old_repo():
    with patch("daily_ai_digest.search._github_repo_age_days", return_value=200):
        items = _filter_stale_repos([{"url": "https://github.com/old/repo"}])
        assert items == []


def test_filter_stale_repos_keeps_recent_repo():
    with patch("daily_ai_digest.search._github_repo_age_days", return_value=10):
        items = _filter_stale_repos([{"url": "https://github.com/new/repo"}])
        assert len(items) == 1


def test_filter_stale_repos_keeps_item_when_age_unknown():
    with patch("daily_ai_digest.search._github_repo_age_days", return_value=None):
        items = _filter_stale_repos([{"url": "https://example.com/not-a-repo"}])
        assert len(items) == 1


def test_github_repo_age_days_non_github_url_returns_none():
    from daily_ai_digest.search import _github_repo_age_days
    assert _github_repo_age_days("https://example.com/foo/bar") is None


def test_github_repo_age_days_api_error_returns_none():
    from daily_ai_digest.search import _github_repo_age_days
    with patch("daily_ai_digest.search.get_secret", return_value="fake-token"), \
         patch("daily_ai_digest.search.httpx.get", side_effect=Exception("network down")):
        assert _github_repo_age_days("https://github.com/some/repo") is None


def test_category_labels_derived_from_categories_config():
    assert set(CATEGORY_LABELS.keys()) == {c["key"] for c in CATEGORIES}
    assert len(CATEGORIES) >= 4


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"\n{len(tests)} checks passed")

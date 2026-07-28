"""Self-check for digest-processing fallback and search empty-tolerance logic.
No network calls — mocks the DeepSeek/Tavily boundaries. Run: uv run python test_flow.py
"""
from unittest.mock import MagicMock, patch

from daily_ai_digest.categories import CATEGORIES
from daily_ai_digest.process import (
    CATEGORY_LABELS,
    _attach_published_dates,
    _drop_hallucinated_urls,
    _empty_digest,
    _parse_digest,
    process_results,
)
from daily_ai_digest.search import _normalize


def test_parse_digest_valid():
    text = '{"repos": [{"title": "t", "summary": "s", "url": "u", "source_name": "n"}], "skills": [], "prompting": [], "papers": []}'
    digest = _parse_digest(text)
    assert digest is not None
    assert len(digest["repos"]) == 1
    assert digest["skills"] == []


def test_parse_digest_malformed_returns_none():
    assert _parse_digest("not json") is None


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
    good.choices = [MagicMock(message=MagicMock(content='{"repos": [{"title": "t", "summary": "s", "url": "u", "source_name": "n"}]}'))]

    with patch("daily_ai_digest.process.get_secret", return_value="fake-key"), \
         patch("daily_ai_digest.process.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.side_effect = [Exception("deepseek down"), good]
        digest = process_results.fn({"repos": [{"url": "u", "title": "t", "snippet": "", "published_date": None}]})
        assert len(digest["repos"]) == 1
        assert digest["repos"][0]["title"] == "t"


def test_process_results_empty_digest_when_both_providers_fail():
    with patch("daily_ai_digest.process.get_secret", return_value="fake-key"), \
         patch("daily_ai_digest.process.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.side_effect = Exception("down")
        digest = process_results.fn({"repos": []})
        assert digest == _empty_digest()


def test_search_normalize_handles_empty_results():
    assert _normalize({"results": []}) == []
    assert _normalize({}) == []


def test_search_normalize_maps_fields():
    raw = {"results": [{"title": "T", "url": "U", "content": "C", "published_date": "2026-01-01"}]}
    items = _normalize(raw)
    assert items == [{"title": "T", "url": "U", "snippet": "C", "published_date": "2026-01-01"}]


def test_attach_published_dates_joins_by_url():
    digest = {"repos": [{"title": "t", "url": "u1", "summary": "s"}, {"title": "t2", "url": "unknown", "summary": "s2"}]}
    raw = {"repos": [{"url": "u1", "published_date": "2026-07-28"}]}
    result = _attach_published_dates(digest, raw)
    assert result["repos"][0]["published_date"] == "2026-07-28"
    assert result["repos"][1]["published_date"] is None


def test_drop_hallucinated_urls_removes_unmatched_items():
    digest = {
        "repos": [
            {"title": "real story", "url": "https://real.example/a", "summary": "s"},
            {"title": "mismatched headline", "url": "https://unrelated.example/other-article", "summary": "s2"},
        ]
    }
    raw = {"repos": [{"url": "https://real.example/a", "published_date": None}]}
    result = _drop_hallucinated_urls(digest, raw)
    assert len(result["repos"]) == 1
    assert result["repos"][0]["title"] == "real story"


def test_process_results_drops_item_with_url_not_in_raw_results():
    good = MagicMock()
    good.choices = [MagicMock(message=MagicMock(content=(
        '{"repos": ['
        '{"title": "matches raw", "summary": "s", "url": "https://real.example/a", "source_name": "n"},'
        '{"title": "hallucinated link", "summary": "s2", "url": "https://made-up.example/x", "source_name": "n2"}'
        ']}'
    )))]

    with patch("daily_ai_digest.process.get_secret", return_value="fake-key"), \
         patch("daily_ai_digest.process.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.side_effect = [good]
        raw_by_category = {"repos": [{"url": "https://real.example/a", "title": "raw title", "snippet": "", "published_date": None}]}
        digest = process_results.fn(raw_by_category)
        assert len(digest["repos"]) == 1
        assert digest["repos"][0]["title"] == "matches raw"


def test_category_labels_derived_from_categories_config():
    assert set(CATEGORY_LABELS.keys()) == {c["key"] for c in CATEGORIES}
    assert len(CATEGORIES) >= 4


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"\n{len(tests)} checks passed")

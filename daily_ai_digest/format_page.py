from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader
from prefect import task

from daily_ai_digest.process import CATEGORY_LABELS

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(_TEMPLATES_DIR))


_ROMAN = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
    (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
]


def _to_roman(n: int) -> str:
    result = []
    for value, symbol in _ROMAN:
        count, n = divmod(n, value)
        result.append(symbol * count)
    return "".join(result)


def _volume_and_issue(editions: list[dict], iso_date: str) -> tuple[int, int]:
    """Volume increments once per calendar month of publish history; issue number
    resets to 1 at the start of each new volume and counts editions within that month.
    A rerun of today reuses today's already-stored numbers instead of incrementing again."""
    today_entry = next((e for e in editions if e["iso_date"] == iso_date), None)
    if today_entry and "volume_num" in today_entry and "issue" in today_entry:
        return today_entry["volume_num"], today_entry["issue"]

    month = iso_date[:7]
    same_month_others = [e for e in editions if e["iso_date"][:7] == month and e["iso_date"] != iso_date]
    past_months = sorted({e["iso_date"][:7] for e in editions if e["iso_date"][:7] < month})
    volume_num = len(past_months) + 1
    issue = len(same_month_others) + 1
    return volume_num, issue


def _build_sections_and_lead(digest: dict) -> tuple[list[dict], dict | None]:
    """Front page needs one lead story (pulled out of its section) plus the
    remaining sections with per-section item counts, so the template can
    give the lead outsized display and skip empty sections in the index."""
    lead = None
    sections = []
    for category, label in CATEGORY_LABELS.items():
        items = list(digest.get(category, []))
        if not items:
            continue
        if lead is None:
            lead = {"category": category, "label": label, "item": items[0]}
            items = items[1:]
        if items:
            sections.append({"category": category, "label": label, "count": len(items), "entries": items})
    return sections, lead


@task
def render_page(digest: dict, editions: list[dict]) -> tuple[str, dict]:
    """Returns (html, meta) where meta carries the fields the archive index needs
    (iso_date, display date/time, lead headline, volume/issue) without re-deriving
    them later. `editions` is prior publish history, used to compute Vol./No."""
    template = _env.get_template("edition.html")
    now = datetime.now(ZoneInfo("Asia/Calcutta"))
    iso_date = now.date().isoformat()
    sections, lead = _build_sections_and_lead(digest)
    date_display = now.strftime("%B %d, %Y").replace(" 0", " ")
    updated_at = now.strftime("%I:%M %p IST").lstrip("0")
    volume_num, issue = _volume_and_issue(editions, iso_date)
    html = template.render(
        sections=sections,
        lead=lead,
        date=date_display,
        updated_at=updated_at,
        volume=_to_roman(volume_num),
        issue=issue,
    )
    meta = {
        "iso_date": iso_date,
        "date": date_display,
        "updated_at": updated_at,
        "headline": lead["item"]["title"] if lead else None,
        "volume_num": volume_num,
        "issue": issue,
    }
    return html, meta

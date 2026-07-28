from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader
from prefect import task

from daily_ai_digest.process import CATEGORY_LABELS

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(_TEMPLATES_DIR))


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
def render_page(digest: dict) -> tuple[str, str]:
    """Returns (html, today's ISO date string)."""
    template = _env.get_template("edition.html")
    now = datetime.now(ZoneInfo("Asia/Calcutta"))
    sections, lead = _build_sections_and_lead(digest)
    html = template.render(
        sections=sections,
        lead=lead,
        date=now.strftime("%B %d, %Y").replace(" 0", " "),
        updated_at=now.strftime("%I:%M %p IST").lstrip("0"),
    )
    return html, now.date().isoformat()

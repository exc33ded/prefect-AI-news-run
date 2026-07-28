from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from prefect import task

from daily_ai_digest.process import CATEGORY_LABELS

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(_TEMPLATES_DIR))


EMAIL_ITEMS_PER_CATEGORY = 2


@task
def render_email(digest: dict, edition_url: str) -> str:
    template = _env.get_template("email.html")
    highlights = {category: items[:EMAIL_ITEMS_PER_CATEGORY] for category, items in digest.items()}
    remaining_counts = {
        category: max(len(items) - EMAIL_ITEMS_PER_CATEGORY, 0) for category, items in digest.items()
    }
    return template.render(
        digest=highlights,
        remaining_counts=remaining_counts,
        category_labels=CATEGORY_LABELS,
        date=date.today().strftime("%B %d, %Y").replace(" 0", " "),
        edition_url=edition_url,
    )

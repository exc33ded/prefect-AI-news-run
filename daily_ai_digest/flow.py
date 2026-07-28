from prefect import flow, get_run_logger

from daily_ai_digest.config import get_secret
from daily_ai_digest.format_email import render_email
from daily_ai_digest.format_page import render_page
from daily_ai_digest.notify import send_email
from daily_ai_digest.process import process_results
from daily_ai_digest.publish_github import publish_page
from daily_ai_digest.search import submit_all_searches


def _edition_url() -> str:
    repo = get_secret("GITHUB_REPO")
    owner, name = repo.split("/")
    return f"https://{owner}.github.io/{name}/"


@flow(log_prints=True)
def daily_ai_digest():
    logger = get_run_logger()

    futures = submit_all_searches()
    logger.info(f"Started parallel search across {len(futures)} categories")

    raw_by_category = {}
    for category, future in futures.items():
        try:
            raw_by_category[category] = future.result()
        except Exception as e:
            logger.warning(f"Search for '{category}' failed: {e}")
            raw_by_category[category] = []
        print(f"{category}: {len(raw_by_category[category])} raw results")

    logger.info("Processing results with LLM")
    digest = process_results(raw_by_category)
    for category, items in digest.items():
        print(f"{category}: {len(items)} digest items")

    logger.info("Rendering email and page")
    edition_url = _edition_url()
    email_html = render_email(digest, edition_url)
    page_html, iso_date = render_page(digest)

    logger.info("Delivering email")
    try:
        send_email(email_html, iso_date)
        print("Email sent")
    except Exception as e:
        logger.warning(f"Email delivery failed: {e}")

    logger.info("Publishing GitHub Pages edition")
    try:
        publish_page(page_html, iso_date)
        print("GitHub Pages published")
    except Exception as e:
        logger.warning(f"GitHub publish failed: {e}")

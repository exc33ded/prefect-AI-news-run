import resend
from prefect import task

from daily_ai_digest.config import get_secret


@task(retries=2, retry_delay_seconds=[5, 15])
def send_email(html: str, date: str) -> None:
    resend.api_key = get_secret("RESEND_API_KEY")

    try:
        email_from = get_secret("EMAIL_FROM")
    except Exception:
        email_from = "onboarding@resend.dev"

    resend.Emails.send(
        {
            "from": email_from,
            "to": get_secret("EMAIL_TO"),
            "subject": f"THE AI DAILY — {date}",
            "html": html,
        }
    )

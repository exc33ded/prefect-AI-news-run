# Email Delivery

How the daily digest reaches your inbox — the Resend integration, email template rendering, retry logic, and troubleshooting.

---

## Overview

The email delivery pipeline takes the processed digest, renders it into a vintage-newspaper-styled HTML email using Jinja2, and sends it via the Resend API. The entire flow from digest to inbox takes 3-8 seconds.

```
digest (processed results)
  │
  ▼
render_email(digest, edition_url)  ← @task in format_email.py
  │
  ├── Top 2 items per category extracted
  ├── Jinja2 template rendered (templates/email.html)
  └── Returns: HTML string
  │
  ▼
send_email(email_html, date_str)  ← @task(retries=2) in notify.py
  │
  ├── Resend API call
  ├── Subject: "THE AI DAILY — 2026-01-30"
  └── Delivered to EMAIL_TO
```

---

## Key Functions

### `render_email()` — Template Rendering

```python
@task
def render_email(digest: dict, edition_url: str) -> str:
    """Render the email from Jinja2 template. Shows top 2 per category."""
    from jinja2 import Environment, PackageLoader

    top_two = {}
    for key, items in digest.items():
        top_two[key] = items[:2]

    labels = {cat["key"]: cat["label"] for cat in CATEGORIES}

    env = Environment(loader=PackageLoader("daily_ai_digest", "templates"))
    template = env.get_template("email.html")
    return template.render(
        date=datetime.now().strftime("%B %d, %Y"),
        edition_url=edition_url,
        categories=top_two,
        category_labels=labels,
        ...
    )
```

**Design decision: Top 2 per category.** The email is a preview — the full edition lives on the website. Showing only 2 items per category keeps the email scannable in under 5 minutes. The "+N more" links drive traffic to the web edition.

---

### `send_email()` — Delivery

```python
@task(retries=2, retry_delay_seconds=[5, 15])
def send_email(email_html: str, date_str: str):
    import resend

    resend.api_key = get_secret("RESEND_API_KEY")

    params = {
        "from": get_secret("EMAIL_FROM") or "onboarding@resend.dev",
        "to": [get_secret("EMAIL_TO")],
        "subject": f"THE AI DAILY — {date_str}",
        "html": email_html,
    }

    resend.Emails.send(params)
```

**Defaults:**
- `EMAIL_FROM` defaults to `onboarding@resend.dev` if not set — this works on free tier
- `EMAIL_TO` is required — if missing, the task fails
- Subject format: `THE AI DAILY — YYYY-MM-DD`

**Retry behavior:**
- Two retries with 5-second and 15-second delays
- Common transient failures: Resend API timeout, rate limit, temporary DNS issues
- If all retries fail, the flow catches the exception and continues (publishing still happens)

---

## Email Template Structure

The email uses `templates/email.html` (~200 lines, inline CSS only).

### Layout Sections

```
┌──────────────────────────────────────┐
│ MASTHEAD                             │
│ ───────                              │
│ THE AI HERALD                        │  ← Large, centered, serif font
│ "All the AI News That's Fit to Print" │  ← Italic tagline
│ January 30, 2026                     │  ← Dateline
│                                      │
│ ⚠ AI-GENERATED CONTENT DISCLAIMER   │  ← Small text, italic
│                                      │
│ ──────────────────────────────────── │
│                                      │
│ ✦ REPOS ✦                           │  ← Category header
│ ──────                               │
│                                      │
│ Story 1 Headline                     │  ← Linked to source
│ Source: github.com | Jan 30, 2026   │  ← Meta line
│                                      │  ← Summary paragraph (3-5 sentences)
│ Summary text goes here...            │
│                                      │
│ Story 2 Headline                     │
│ Source: github.com | Jan 29, 2026   │
│ Summary text goes here...            │
│                                      │
│ +3 more stories                      │  ← Link to full web edition
│                                      │
│ ✦ SKILLS ✦                          │  ← Next category
│ ... (same pattern) ...               │
│                                      │
│ ┌────────────────────────────────┐   │
│ │   READ TODAY'S FULL EDITION    │   │  ← CTA button
│ │   →                             │   │
│ └────────────────────────────────┘   │
│                                      │
│ FOOTER                               │
│ ──────                               │
│ The AI Herald is an AI-generated...  │
│ Unsubscribe | Archive                │
└──────────────────────────────────────┘
```

### Why Inline CSS Only

Email clients (Gmail, Outlook, Apple Mail) all handle CSS differently:
- Some strip `<style>` blocks (Outlook)
- Some ignore external stylesheets (all)
- Some don't support flexbox or grid (Outlook)
- Dark mode can override colors unpredictably

The template uses only inline CSS (`style="..."` attributes) to maximize compatibility. This means:
- No `<style>` blocks
- No `<link>` to external CSS
- No CSS variables
- Table-based layout where needed
- Web-safe fonts (`Georgia`, `Times New Roman`, `serif`)

### Dark Mode Compatibility

No special dark mode handling. Inline CSS with explicit `background-color` and `color` on every element ensures the email looks the same in dark and light modes. This is intentional — the vintage newspaper aesthetic uses parchment/paper colors that look wrong when inverted.

---

## Resend Free Tier Limits

| Limit | Value | Pipeline Usage |
|-------|-------|---------------|
| Emails per day | 100 | 1 per run |
| Emails per month | 3,000 | ~31 per month |
| Verified domains | 1 (free) | Not needed if using `onboarding@resend.dev` |
| Custom domain | Paid only | Not needed |
| Recipients | Account email only (free) | `EMAIL_TO` must match your Resend email |

**The key limitation:** On the free tier, Resend only sends to the email address associated with your Resend account. If you set `EMAIL_TO` to a different address, the email will be silently dropped.

**To send to other addresses:**
1. In Resend dashboard → Domains → Add Domain
2. Verify domain ownership (DNS records)
3. Set `EMAIL_FROM` to an address on that domain
4. Upgrade to a paid plan if you need more than 100 emails/day

---

## Delivery Flow

```
┌─────────────┐
│  digest      │
└──────┬──────┘
       ▼
┌─────────────┐
│ extract      │  ← Top 2 items per category
│ top 2        │
└──────┬──────┘
       ▼
┌─────────────┐
│ Jinja2       │  ← Render templates/email.html
│ render       │
└──────┬──────┘
       ▼
┌─────────────┐
│ Resend API   │  ← send(html)
│ POST         │
└──────┬──────┘
       │
  ┌────▼────┐
  │ Success? │─── YES ──→ Done (inbox)
  └────┬────┘
       │ NO
       ▼
  ┌─────────┐
  │ Retry 1 │ ──→ Wait 5s, try again
  └────┬────┘
       │ Still fails
       ▼
  ┌─────────┐
  │ Retry 2 │ ──→ Wait 15s, try again
  └────┬────┘
       │ Still fails
       ▼
  ┌───────────────┐
  │ Log error     │ ──→ Flow continues (other stages unaffected)
  │ Email skipped  │
  └───────────────┘
```

---

## Modifying Email Behavior

### Change Email Subject

Edit `notify.py`:

```python
"subject": f"AI NEWS DIGEST — {date_str}",  # Custom subject
```

### Change Sender Name

Edit `notify.py`:

```python
"from": "The AI Herald <onboarding@resend.dev>",
```

(Requires a verified domain on Resend paid plan.)

### Change Email to Plain Text

Replace the HTML with text:

```python
params = {
    "from": get_secret("EMAIL_FROM") or "onboarding@resend.dev",
    "to": [get_secret("EMAIL_TO")],
    "subject": f"THE AI DAILY — {date_str}",
    "text": plain_text_version,  # Instead of "html"
}
```

### Add Multiple Recipients

```python
"to": [
    get_secret("EMAIL_TO"),
    "colleague@example.com",
    "team@example.com",
],
```

On free tier, all recipients must be your Resend account email.

---

## Troubleshooting

### "Email not received"

**Checklist:**
1. Confirm the flow log shows "Sending email... Done!"
2. Check spam/junk folder
3. Verify `EMAIL_TO` matches your Resend account email (free tier limitation)
4. Check Resend dashboard → Emails → check for bounced/dropped events
5. Verify `RESEND_API_KEY` is correct

### "Email looks broken in Outlook"

Outlook uses Word's rendering engine (not a browser engine). Specific fixes:
- Avoid `background-image` (Outlook doesn't support it)
- Use `border` instead of `box-shadow` (Outlook ignores shadows)
- Ensure all images have explicit width/height attributes
- Test with [Litmus](https://litmus.com) or [Email on Acid](https://emailonacid.com) for comprehensive client testing

### "Resend returns 403 Forbidden"

- Your API key is invalid or expired
- Your Resend account may be in trial/suspended mode
- Check Resend dashboard for any account alerts

### "Gmail clips the email (shows 'View entire message')"

Gmail clips emails over 102KB. With 10 categories and summaries, this can happen. Mitigation:
- Reduce items per category (show top 1 instead of top 2)
- Shorten summaries
- Use text compression in the template

---

## Next Steps

- How the website is published → **[GitHub Pages Publishing](11-github-pages-publishing.md)**
- Understand the email template → **[Email Template](../../frontend/20-email-template.md)**
- Fix delivery issues → **[Troubleshooting](17-troubleshooting.md)**

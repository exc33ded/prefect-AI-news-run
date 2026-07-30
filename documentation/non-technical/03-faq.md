# FAQ

Answers to the most common questions about The AI Herald.

---

## General

### What exactly is this project?

A fully automated daily AI news digest. It searches 10 categories of AI news every morning, uses AI to summarize the stories, and delivers the results as a vintage-newspaper-styled email and website. Everything runs on autopilot — no human intervention needed.

### Who is this for?

Anyone interested in staying up-to-date with AI developments without manually browsing 20 different sites. Developers, researchers, product managers, AI enthusiasts. The email takes 5 minutes to scan. The web edition is there for deeper dives.

### Is this a commercial product?

No. It's an open-source project. You can use it as-is, fork it, modify it, run it yourself. The published website is a public demonstration.

### How do I subscribe?

If you're the person running the pipeline, you configure the `EMAIL_TO` address in your secrets. If someone else is running it, ask them to add your email. There's no self-service subscription system — the pipeline sends to exactly one configured address.

---

## Technical

### Why Prefect? What is it?

**Prefect** is a workflow orchestration platform. Think of it as a smart cron job scheduler that:

- Runs your code on a schedule (e.g., every day at 8 AM)
- Retries things that fail
- Shows you logs and run history in a web dashboard
- Handles secrets (API keys) so they don't live in your code
- Provides a "managed" work pool where Prefect runs your code on its own infrastructure — no server needed

Before Prefect, you'd need to set up a cron job, handle retries yourself, store secrets somewhere secure, and figure out where to host it. Prefect handles all of that.

### Do I need Prefect Cloud to run this?

**No.** You can run the entire pipeline locally with:

```bash
uv run python main.py
```

Prefect Cloud is only needed for the automated daily schedule. If you just want to run it manually or set up your own cron job, you don't need Prefect at all.

### Why two AI providers (DeepSeek and Groq)?

**Resilience.** If DeepSeek has an outage (it happens), the pipeline automatically falls back to Groq. No interruption, no failed digest.

DeepSeek is used as the primary because:
- It's the most cost-effective ($0.0001 per request)
- Good quality summaries for this use case

Groq is the fallback because:
- Free tier with generous rate limits
- Different infrastructure (less likely to be down at the same time as DeepSeek)

If both are down (extremely rare), the digest is still delivered — just without AI summaries. You'll see raw search results with headlines and URLs intact.

### How much does it cost to run?

Very little. Here's the breakdown per run:

| Service | Cost per Run | Notes |
|---------|-------------|-------|
| Tavily | Free (under 1,000/month) | Free tier: 1,000 searches/month; pipeline uses ~10/run |
| DeepSeek | ~$0.001 | ~10 LLM requests at ~$0.0001 each |
| Groq | Free | Free tier — only used when DeepSeek fails |
| Resend | Free (under 100/day) | Free tier: 100 emails/day; pipeline uses 1/run |
| Prefect Cloud | Free (Hobby tier) | Hobby tier: 1 managed work pool, unlimited runs |
| GitHub Pages | Free | Public repos get free hosting |

**Total cost: ~$0.001 per run** (about $0.37/year). Effectively free.

### How do I add a new search category?

See **[Extending the System](../technical/backend/extending-the-system.md)**. Quick answer: add one entry to `categories.py`, then re-deploy. Everything else propagates automatically.

### What happens if the search fails for one category?

Nothing breaks. Each category is searched independently. If one fails, the other 9 still work. The failing category returns empty results and shows `(no results found)` in the digest. The pipeline never crashes because one category had an issue.

### How do search results get from Tavily to the email?

1. Tavily searches each category → returns raw results (title, URL, snippet, date)
2. Results are assigned positional IDs
3. Sent to DeepSeek: "Pick the most relevant stories by ID and write summaries"
4. The AI returns `{id: 3, summary: "..."}` — notice: no titles, no URLs
5. The pipeline resolves IDs back to raw data to get real titles and URLs
6. Rendered into HTML templates via Jinja2
7. Sent via Resend (email) and GitHub Contents API (website)

The key design decision: **the AI never writes headlines or URLs.** This prevents hallucinated links and made-up story titles. Every headline and URL comes directly from Tavily search results.

### Why do I see repos older than 90 days sometimes?

Only the `repos` category applies the 90-day freshness filter. If Tavily returns an older repo in another category (e.g., `trends` or `industry_news`), it won't be filtered. This is intentional — older repos can be relevant in non-repo categories.

### How does the Volume/Issue numbering work?

- **Volume** = calendar months since the pipeline's first edition (Roman numerals: I, II, III...)
- **Issue** = how many editions published this month so far (starts at 1 each month)

So `Vol. III, No. 17` means "month 3 of operation, 17th edition this month."

The numbers are calculated by reading the archive (all past editions stored in `docs/archive.json`).

### How do I update the AI model (switch from DeepSeek to something else)?

See the model configuration in `process.py`. The model name and base URL are in `_build_openai_client()`. Change the model string and base URL, then re-deploy. The code uses the OpenAI-compatible SDK, so any OpenAI-compatible provider works (OpenAI, Anthropic via proxy, Together, Fireworks, etc.).

---

## Email & Website

### The email looks broken in Gmail/Outlook

Email HTML is notoriously finicky. The template uses inline CSS only (no stylesheets, no external resources) to maximize compatibility. Animations and advanced styling are stripped from the email version — it's deliberately simpler than the website.

If you're seeing issues, check:
- Is the email being sent as HTML? (It should be — the Resend SDK sends HTML by default)
- Is your email client blocking remote content? (There shouldn't be any — it's all inline)
- Does it look different in another email client? (This helps isolate whether it's a template issue or client-specific)

### Can I change how the website looks?

Yes. The website is built from three Jinja2 templates:

- `daily_ai_digest/templates/edition.html` — the daily edition page
- `daily_ai_digest/templates/email.html` — the email
- `daily_ai_digest/templates/archive.html` — the archive/calendar page

See the **[Frontend Documentation](../technical/frontend/design-system.md)** for a complete breakdown of how the templates work, the CSS variables you can change, and how to add new features.

### Does the archive page automatically update?

Yes. Every time the pipeline runs, it:
1. Appends the new edition's metadata to `docs/archive.json`
2. Regenerates `docs/archive.html` from the updated archive

The archive page is always current — no manual updates needed.

### Why does the website use `data-theme` for dark mode instead of `prefers-color-scheme`?

Because `prefers-color-scheme` follows the OS/browser setting, and we want the user to be able to toggle manually on the page. The default theme is `light` (newspaper aesthetic), and users can switch to dark mode with the 🌙 button. The choice persists for the session (localStorage is planned).

### Can I host the website somewhere other than GitHub Pages?

Yes. The pipeline writes HTML files to `docs/`. You can point any static site host (Netlify, Vercel, Cloudflare Pages, S3) at that directory. Just change the `publish_page()` function in `publish_github.py` to use your host's API instead of GitHub Contents API — or simply serve the `docs/` directory as-is with any web server.

---

## Troubleshooting

### "I ran the pipeline but no email arrived"

Check (in order):

1. **Did the console show "Sending email... Done!"?** If not, there was an error — read the console output.
2. **Check your spam folder.** New sender addresses often land in spam.
3. **Is `EMAIL_TO` set to your Resend account email?** On the free Resend tier, you can only send to your own account email unless you've verified a custom domain.
4. **Is `RESEND_API_KEY` correct?** Double-check the key in your Resend dashboard.
5. **Try sending a test email with Resend's API directly** to confirm your key works.

### "I get a DeepSeek authentication error"

The most common causes:
- Your DeepSeek API key is stored in `OPENAI_API_KEY` (not a `DEEPSEEK_` key) — the code uses the OpenAI-compatible SDK with `base_url=https://api.deepseek.com`, so the key goes in `OPENAI_API_KEY`
- Your key has expired or been revoked — regenerate it in the DeepSeek dashboard
- You haven't added billing to your DeepSeek account — free credits may have run out

### "Tavily search returns no results for some categories"

This is normal occasionally. AI news moves fast, and some days a category genuinely has nothing new. The digest will show `(no results found)` for that category and move on.

If it happens consistently for the same category, the search query may need updating. Search queries are in `categories.py` — tweak the `query` field to be more specific or broader.

### "I changed the code but the changes don't take effect on Prefect Cloud"

You need to push to GitHub AND re-deploy:

```bash
git add .
git commit -m "your message"
git push
uv export --frozen --no-dev --no-editable -o requirements.txt
prefect deploy --name daily-ai-digest
```

If you only pushed to GitHub but didn't re-deploy, Prefect Cloud still has the old deployment configuration. The `prefect deploy` command tells Prefect Cloud "use this code at this commit."

If you only re-deployed but didn't push, Prefect Cloud will try to pull code from GitHub that doesn't exist yet.

### "Where do I see the logs for Prefect Cloud runs?"

Go to [app.prefect.cloud](https://app.prefect.cloud) → your workspace → Flow Runs → click on any run. You'll see all `print()` output from the flow, task statuses, retry counts, and error messages.

The flow uses `@flow(log_prints=True)`, so every `print()` statement inside the flow appears in Prefect's log viewer.

### "How do I trigger a manual run on Prefect Cloud?"

```bash
prefect deployment run "daily-ai-digest/daily-ai-digest"
```

Or from the Prefect Cloud UI: Deployments → "daily-ai-digest" → Run → confirm.

---

## Extending

### How do I add another email recipient?

Modify `notify.py` — the `send_email` task has a `to_emails` parameter. Change it from a single address to a list:

```python
params = {
    "from": get_secret("EMAIL_FROM") or "onboarding@resend.dev",
    "to": [get_secret("EMAIL_TO"), "colleague@example.com"],
    "subject": f"THE AI DAILY — {date_str}",
    "html": email_html
}
```

On the free Resend tier, additional recipients must be verified.

### How do I change the schedule?

Edit `prefect.yaml` and change the `cron` and `timezone` fields:

```yaml
schedules:
  - cron: "0 8 * * *"
    timezone: "Asia/Calcutta"
```

Then re-deploy: `prefect deploy --name daily-ai-digest`

Cron format: `minute hour day_of_month month day_of_week`
- `0 8 * * *` = every day at 8:00 AM
- `0 12 * * 1-5` = every weekday at noon
- `0 0 * * 0` = every Sunday at midnight

### How do I add more Tavily API keys for better reliability?

Add them to your `.env` file:

```bash
TAVILY_API_KEY_5=sk-your-key-here
TAVILY_API_KEY_6=sk-another-key-here
```

The search system reads `TAVILY_API_KEY_1` through `TAVILY_API_KEY_10`. It tries keys sequentially: if key 1 fails, it tries key 2, and so on. This provides resilience against rate limits on individual keys.

For Prefect Cloud, add the keys as Secret blocks using the same naming convention:

```bash
python -c "from prefect.blocks.system import Secret; Secret(value='sk-...').save('tavily-api-key-5', overwrite=True)"
```

---

## Still Have Questions?

Check the **[Technical Documentation](../technical/00-index.md)** for deep dives into every system component, or the **[Troubleshooting Guide](../technical/backend/troubleshooting.md)** for problem-specific solutions.

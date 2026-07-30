# Troubleshooting

A decision-tree guide to diagnosing and fixing common issues. Start at the symptom, follow the branches.

---

## Quick Diagnostic

Before diving into specific problems, run this checklist:

```bash
# 1. Is Prefect Cloud reachable?
prefect version

# 2. Is the work pool healthy?
prefect work-pool ls

# 3. Is the deployment active?
prefect deployment inspect "daily-ai-digest/daily-ai-digest" 2>/dev/null || echo "Not found"

# 4. What ran recently?
prefect flow-run ls --limit 5

# 5. Are secrets in place?
prefect block ls 2>/dev/null | grep secret || echo "Run locally: uv run python -c \"from daily_ai_digest.config import get_secret; print(get_secret('TAVILY_API_KEY_1')[:10])\""
```

---

## Decision Tree

```
Problem detected
  │
  ├── Flow never runs? ──→ SCHEDULE ISSUES
  │
  ├── Flow runs but no email? ──→ EMAIL ISSUES
  │
  ├── Flow runs but website not updated? ──→ PUBLISHING ISSUES
  │
  ├── Flow runs but digest is empty/wrong? ──→ CONTENT ISSUES
  │
  ├── Flow crashed mid-run? ──→ RUNTIME ERRORS
  │
  └── Something else? ──→ GENERAL
```

---

## Schedule Issues

### Symptom: Flow never starts at scheduled time

**Check:**

```bash
prefect deployment inspect "daily-ai-digest/daily-ai-digest"
```

Look for:
- `"is_schedule_active": true` — if `false`, activate it in the UI
- `"schedules": [{"cron": "0 8 * * *", "timezone": "Asia/Calcutta"}]` — correct?

**Also check:**
- Work pool status: `prefect work-pool ls` → must be `READY`
- If pool is `NOT_READY` or missing, recreate: `prefect work-pool create ai-digest-managed-pool --type prefect:managed`
- Check [status.prefect.io](https://status.prefect.io) for Prefect Cloud incidents

### Symptom: Flow runs at wrong time

**Check timezone:** Is `timezone: "Asia/Calcutta"` correct? IST is UTC+5:30.

**Check cron:** `0 8 * * *` = 8:00 AM. `0 14 * * *` = 2:00 PM.

### Symptom: Flow stuck on "Late" or "Scheduled"

The managed work pool may be at capacity (Hobby tier: 1 concurrent run). Check:
- Are there other runs still active? `prefect flow-run ls --limit 10`
- Cancel stuck runs: `prefect flow-run cancel <id>`

If the pool itself is stuck, recreate the deployment:

```bash
prefect deploy --name daily-ai-digest
```

---

## Email Issues

### Symptom: Flow logs say "Sending email... Done!" but nothing arrives

**Checklist:**

1. **Check spam folder.** New senders often land in spam.
2. **Verify Resend free tier limitation.** On free tier, can only send to your Resend account email. If `EMAIL_TO` is different, the email is silently dropped.
3. **Check Resend dashboard** → Emails → look for the sent email. If it shows `delivered` but you don't see it, it's a client-side issue.
4. **Verify email address.** Typos happen more often than you'd think.

### Symptom: Flow logs show "Email stage failed"

**Read the error message** in Prefect Cloud logs:

- **"401 Unauthorized"** → `RESEND_API_KEY` is wrong or expired
- **"403 Forbidden"** → Your Resend account may be suspended or over limit
- **"Connection timeout"** → Network issue. Prefect container may have restricted outbound access.

**Fix:**

```bash
# Update the secret
python -c "from prefect.blocks.system import Secret; Secret(value='re_correct_key').save('resend-api-key', overwrite=True)"
```

### Symptom: Email looks wrong (broken styling)

- If in Gmail: Gmail strips `<style>` blocks. Make sure all CSS is inline.
- If in Outlook: Outlook uses Word's rendering engine. Avoid `background-image`, `box-shadow`, `flexbox`, `grid`.
- Test the email HTML locally: open `docs/index.html` in a browser, then copy the HTML and paste into an email client.

---

## Publishing Issues

### Symptom: Flow logs show "Publishing skipped (no token)"

You don't have `GITHUB_TOKEN` or `GITHUB_REPO` configured.

```bash
# Add the secrets
python -c "from prefect.blocks.system import Secret; Secret(value='ghp_your_token').save('github-token', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='owner/repo').save('github-repo', overwrite=True)"
```

### Symptom: Flow logs show "Failed: docs/index.html (401)"

GitHub token is invalid. Regenerate at GitHub → Settings → Developer settings → Personal access tokens.

**Required scopes:** `repo` (full control of private repositories).

### Symptom: "Published" in logs but website shows old content

1. **GitHub Pages build delay.** Wait 1-2 minutes after the pipeline finishes.
2. **Check build status:** Repository → Actions → "pages build and deployment"
3. **Hard refresh browser:** Ctrl+Shift+R (Windows) / Cmd+Shift+R (Mac)
4. **Check `docs/index.html` on GitHub** to confirm the file was updated
5. **Check Pages source settings:** Repository → Settings → Pages → Source must be "Deploy from a branch" → `main` → `/docs`

### Symptom: "Failed: docs/index.html (409 Conflict)"

Someone/something else modified the file between the pipeline's GET (SHA read) and PUT (write). This is rare. If persistent:
- Check for other automation writing to `docs/`
- Make sure only one deployment is active

---

## Content Issues

### Symptom: Digest shows "(no results)" for a category

Normal occasionally — some days a category genuinely has nothing new. If persistent:

1. **Check the search query** in `categories.py`. Try broadening or narrowing it.
2. **Test the query directly:**
   ```bash
   uv run python -c "
   from tavily import TavilyClient
   from daily_ai_digest.config import get_secret
   c = TavilyClient(api_key=get_secret('TAVILY_API_KEY_1'))
   r = c.search('new AI tools released today 2026 GitHub', max_results=5)
   for item in r['results']: print(item['title'])
   "
   ```
3. **Check if the Tavily key is exhausted** (free tier: 1,000 searches/month)

### Symptom: Digest shows "no news found today" (all categories empty)

All 10 searches returned nothing. This suggests:
- Tavily API is down → check [status.tavily.com](https://status.tavily.com)
- All Tavily keys are exhausted (rate limited)
- Search queries are too restrictive

### Symptom: Digest has headlines but no summaries

The LLM providers both failed. The digest shows raw search results (titles/URLs only, no summaries).

**Check:**
- `OPENAI_API_KEY` is valid (DeepSeek)
- `GROQ_API_KEY` is valid (Groq)
- Both providers may be experiencing outages (rare)

### Symptom: Summaries seem low quality or inaccurate

- LLMs can misinterpret search snippets. This is inherent to the approach.
- Try changing the model in `process.py` (e.g., `deepseek-v4-chat` instead of `deepseek-v4-flash`)
- Adjust temperature: lower (0.1) = more factual but boring; higher (0.5) = more creative but less accurate

---

## Runtime Errors

### Symptom: "ModuleNotFoundError: No module named 'X'"

A dependency is missing from `requirements.txt`. Re-export:

```bash
uv export --frozen --no-dev --no-editable -o requirements.txt
git add requirements.txt && git commit -m "Update requirements" && git push
prefect deploy --name daily-ai-digest
```

### Symptom: "Secret 'X' not found"

The secret block doesn't exist in Prefect Cloud:

```bash
python -c "from prefect.blocks.system import Secret; Secret(value='your_key').save('missing-secret-name', overwrite=True)"
```

### Symptom: "KeyError" or "AttributeError" in logs

A code bug. Check the full traceback in Prefect Cloud logs. Common causes:
- Changed the data structure but didn't update templates
- Category key mismatch between `categories.py` and accessing code
- Template variable name mismatch

### Symptom: Flow runs fine locally but fails on Prefect Cloud

Differences to check:
1. **Secrets:** Are Prefect Cloud secret blocks different from `.env` values?
2. **Dependencies:** Is `requirements.txt` synced? Run `uv export` again.
3. **Code:** Did you push to GitHub? Prefect clones from GitHub, not local files.
4. **Network:** Some APIs may be restricted from Prefect's container IPs (unlikely but possible).

---

## General

### Symptom: "prefect: command not found"

uv isn't activating properly, or prefence isn't installed:

```bash
uv sync               # Re-install all dependencies
uv run prefect version # Verify
```

### Symptom: "Permission denied" on GitHub API calls

- Token doesn't have `repo` scope → regenerate with correct scopes
- Token is for a different account than the repo
- Repository is private and token doesn't have access

### Symptom: "Rate limit exceeded" from GitHub API

Authenticated rate limit is 5,000/hour. Pipeline uses ~7 calls/run. Should never hit this. If you are:
- Someone else is using the same token
- Multiple deployments running simultaneously

### Symptom: Nothing is working and you're lost

1. **Run locally first:** `uv run python main.py` — isolate whether it's a code issue or infrastructure issue
2. **Check all secrets:** Run the `test_flow.py` test suite — it doesn't need network
3. **Read the logs:** Prefect Cloud UI → Flow Runs → click the failed run → see exact error
4. **Check external service status:**
   - [status.prefect.io](https://status.prefect.io)
   - [status.tavily.com](https://status.tavily.com) — not an official page, but check their docs
   - [status.resend.com](https://status.resend.com)
   - [www.githubstatus.com](https://www.githubstatus.com)

---

## Still Stuck?

Check these docs for detailed explanations:
- [Architecture Overview](02-architecture-overview.md) — understand the whole system
- [Resilience & Error Handling](15-resilience-and-errors.md) — how failures work
- [API Keys & Secrets](05-api-keys-and-secrets.md) — secret configuration
- [Command Cheatsheet](16-command-cheatsheet.md) — all commands

# API Keys & Secrets

Every API key, secret, and credential the pipeline needs. How to get them, how to configure them locally, and how to configure them on Prefect Cloud.

---

## Complete Secret Reference

| Secret Name | Service | Required? | Local (.env) | Prefect Block Name | Purpose |
|-------------|---------|-----------|-------------|--------------------|----------|
| `TAVILY_API_KEY_1` | Tavily | **Yes** | env var | `tavily-api-key-1` | AI news search (primary key) |
| `TAVILY_API_KEY_2` | Tavily | No | env var | `tavily-api-key-2` | AI news search (fallback) |
| `TAVILY_API_KEY_3` .. `TAVILY_API_KEY_10` | Tavily | No | env var | `tavily-api-key-3` .. `tavily-api-key-10` | AI news search (additional fallbacks) |
| `OPENAI_API_KEY` | DeepSeek | **Yes** | env var | `openai-api-key` | LLM summarization (primary) |
| `GROQ_API_KEY` | Groq | No (recommended) | env var | `groq-api-key` | LLM summarization (fallback) |
| `RESEND_API_KEY` | Resend | **Yes** | env var | `resend-api-key` | Email delivery |
| `EMAIL_FROM` | Resend | No | env var | `email-from` | Sender address (defaults to `onboarding@resend.dev`) |
| `EMAIL_TO` | Resend | **Yes** | env var | `email-to` | Recipient address |
| `GITHUB_TOKEN` | GitHub | No | env var | `github-token` | Publishing to GitHub Pages |
| `GITHUB_REPO` | GitHub | No | env var | `github-repo` | Repository name (`owner/repo`) |

---

## How Secrets Are Loaded

All secrets go through a single function in `config.py`:

```python
def get_secret(name: str) -> Optional[str]:
    # Step 1: Try environment variable (local .env)
    value = os.getenv(name)
    if value:
        return value

    # Step 2: Try Prefect Secret block (Prefect Cloud)
    try:
        block_name = name.lower().replace("_", "-")
        block = Secret.load(block_name)
        return block.get()
    except Exception:
        return None
```

**The naming convention:**
- `.env` variables: `UPPERCASE_WITH_UNDERSCORES` (e.g., `TAVILY_API_KEY_1`)
- Prefect Secret blocks: `lowercase-with-hyphens` (e.g., `tavily-api-key-1`)

`get_secret()` handles the conversion automatically. You call `get_secret("TAVILY_API_KEY_1")` and it works in both environments.

---

## Getting Each Key

### Tavily API Keys

**Service:** [Tavily](https://tavily.com) — AI-optimized search API

1. Go to [tavily.com](https://tavily.com) → Sign Up
2. Dashboard → API Keys → Create Key
3. Copy the key

**Why multiple keys?** Each free Tavily key has a 1,000 searches/month limit. The pipeline uses ~300 searches/month (10 categories × 30 days). One key is usually enough. Multiple keys provide resilience — if one key hits a rate limit, the next key takes over seamlessly.

**To add multiple keys (local):**
```bash
# In .env
TAVILY_API_KEY_1=tvly-abc123...
TAVILY_API_KEY_2=tvly-def456...
TAVILY_API_KEY_3=tvly-ghi789...
```

**To add multiple keys (Prefect Cloud):**
```bash
python -c "from prefect.blocks.system import Secret; Secret(value='tvly-abc123...').save('tavily-api-key-1', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='tvly-def456...').save('tavily-api-key-2', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='tvly-ghi789...').save('tavily-api-key-3', overwrite=True)"
```

The system auto-discovers keys by checking `TAVILY_API_KEY_1` through `TAVILY_API_KEY_10`. If key 5 doesn't exist, it stops there.

### DeepSeek API Key

**Service:** [DeepSeek](https://platform.deepseek.com) — LLM API (OpenAI-compatible)

1. Go to [platform.deepseek.com](https://platform.deepseek.com) → Sign Up
2. Add billing (pay-as-you-go) — needed even for the free tier
3. API Keys → Create new key
4. Copy the key

**Important:** The key goes in `OPENAI_API_KEY` (not `DEEPSEEK_API_KEY`). The code uses OpenAI's Python SDK configured with `base_url="https://api.deepseek.com"`, so the key name follows the OpenAI convention.

**Cost:** ~$0.0001 per request. Each daily run uses ~10 requests = ~$0.001/day.

### Groq API Key (Optional, Recommended)

**Service:** [Groq](https://console.groq.com) — Fast LLM inference (OpenAI-compatible)

1. Go to [console.groq.com](https://console.groq.com) → Sign Up
2. API Keys → Create API Key
3. Copy the key

**Cost:** Free tier with generous rate limits. Used as fallback — typically never invoked unless DeepSeek is down.

### Resend API Key

**Service:** [Resend](https://resend.com) — Email API

1. Go to [resend.com](https://resend.com) → Sign Up
2. API Keys → Create API Key
3. Copy the key

**Important:** On the free tier, Resend can only send to the email address associated with your Resend account. If `EMAIL_TO` is different, the email will be silently dropped. To send to other addresses, verify a domain in the Resend dashboard.

### Email Configuration

```bash
# .env
EMAIL_FROM=onboarding@resend.dev     # Default sender (works on free tier)
EMAIL_TO=your.email@gmail.com        # MUST be your Resend account email on free tier
```

If you verify a custom domain with Resend, you can set `EMAIL_FROM` to any address on that domain (e.g., `digest@yourdomain.com`).

### GitHub Token (Optional)

**Service:** GitHub — Personal Access Token

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token → Select scopes: `repo` (full control of private repositories)
3. Copy the token

**Required only if publishing to GitHub Pages.** If omitted, the pipeline runs but skips publishing with a warning.

**Repository configuration:**
```bash
GITHUB_REPO=exc33ded/prefect-AI-news-run   # Format: owner/repo
```

---

## Local Configuration (.env)

The complete `.env` template (`cp .env.example .env`):

```bash
# Tavily Search API Keys (at least one required)
TAVILY_API_KEY_1=your_tavily_key_here
# TAVILY_API_KEY_2=optional_second_key
# TAVILY_API_KEY_3=optional_third_key
# ... up to TAVILY_API_KEY_10

# DeepSeek API (required - primary AI provider)
OPENAI_API_KEY=your_deepseek_key_here

# Groq API (optional - fallback AI provider)
GROQ_API_KEY=your_groq_key_here

# Resend API (required - email delivery)
RESEND_API_KEY=your_resend_key_here

# Email Settings
EMAIL_FROM=onboarding@resend.dev
EMAIL_TO=your_email@example.com

# GitHub (optional - for publishing the web edition)
GITHUB_TOKEN=your_github_pat_here
GITHUB_REPO=exc33ded/prefect-AI-news-run
```

---

## Prefect Cloud Configuration

Secrets are stored as Prefect Secret blocks. The naming convention:

| .env Name | Prefect Block Name |
|-----------|-------------------|
| `TAVILY_API_KEY_1` | `tavily-api-key-1` |
| `OPENAI_API_KEY` | `openai-api-key` |
| `GROQ_API_KEY` | `groq-api-key` |
| `RESEND_API_KEY` | `resend-api-key` |
| `EMAIL_FROM` | `email-from` |
| `EMAIL_TO` | `email-to` |
| `GITHUB_TOKEN` | `github-token` |
| `GITHUB_REPO` | `github-repo` |

### Bulk Setup Commands

Run these AFTER logging into Prefect Cloud (`prefect cloud login`):

```bash
# 1. Tavily key (required)
python -c "from prefect.blocks.system import Secret; Secret(value='tvly-YOUR_KEY').save('tavily-api-key-1', overwrite=True)"

# 2. DeepSeek key (required)
python -c "from prefect.blocks.system import Secret; Secret(value='sk-YOUR_KEY').save('openai-api-key', overwrite=True)"

# 3. Groq key (recommended)
python -c "from prefect.blocks.system import Secret; Secret(value='gsk_YOUR_KEY').save('groq-api-key', overwrite=True)"

# 4. Resend key (required)
python -c "from prefect.blocks.system import Secret; Secret(value='re_YOUR_KEY').save('resend-api-key', overwrite=True)"

# 5. Email sender (optional, defaults to onboarding@resend.dev)
python -c "from prefect.blocks.system import Secret; Secret(value='onboarding@resend.dev').save('email-from', overwrite=True)"

# 6. Email recipient (required)
python -c "from prefect.blocks.system import Secret; Secret(value='you@example.com').save('email-to', overwrite=True)"

# 7. GitHub token (optional, for publishing)
python -c "from prefect.blocks.system import Secret; Secret(value='ghp_YOUR_TOKEN').save('github-token', overwrite=True)"

# 8. GitHub repo (optional, for publishing)
python -c "from prefect.blocks.system import Secret; Secret(value='exc33ded/prefect-AI-news-run').save('github-repo', overwrite=True)"
```

### Verify Secrets

```bash
prefect block ls
```

Should show all the secrets you created.

---

## What Happens If a Secret Is Missing

| Missing Secret | Behavior |
|---------------|----------|
| `TAVILY_API_KEY_1` | No search results → empty digest → email shows "no news found" |
| `TAVILY_API_KEY_2..10` | No fallback for key 1 — if key 1 is rate-limited, search silently fails |
| `OPENAI_API_KEY` (DeepSeek) | Falls back to Groq. If Groq is also missing → empty digest |
| `GROQ_API_KEY` | No fallback for DeepSeek — if DeepSeek fails, empty digest |
| `RESEND_API_KEY` | Email not sent. Pipeline continues (web edition still published if GitHub keys exist) |
| `EMAIL_TO` | Email not sent (no recipient) |
| `GITHUB_TOKEN` | Publishing skipped. Pipeline continues (email still sent) |
| `GITHUB_REPO` | Publishing skipped. Pipeline continues (email still sent) |

The pipeline is designed to be resilient to missing or broken secrets. No single missing secret crashes the entire run.

---

## Security Notes

- **Never commit `.env` to git** — it's in `.gitignore`. Each developer has their own `.env`.
- **Use `.env.example` as a template** — it shows all possible variables without actual values.
- **Prefect Secret blocks are encrypted at rest** — they're stored securely in Prefect Cloud.
- **Secrets never appear in logs** — the code uses `get_secret()` which returns values to memory only.
- **Rotate keys periodically** — especially if you suspect they've been exposed. Update both `.env` and Prefect blocks.

---

## Testing Your Configuration

### Local

```bash
# Test that secrets load correctly
uv run python -c "from daily_ai_digest.config import get_secret; print(get_secret('TAVILY_API_KEY_1')[:10] + '...')"
# Should print: tvly-abcde...
```

### Prefect Cloud

```bash
# Test that a secret block exists
prefect block inspect secret/tavily-api-key-1
# Should show the block metadata (not the value)
```

---

## Next Steps

- Set up your environment → **[Environment Setup](04-environment-setup.md)**
- Set up Prefect Cloud → **[Prefect Cloud Setup](06-prefect-cloud-setup.md)**
- Understand the full secret system → **[Architecture Overview](02-architecture-overview.md)**

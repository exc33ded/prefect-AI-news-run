# Getting Started (Local)

This guide walks you through running **The AI Herald** on your own computer. No Prefect Cloud account, no deployment, no server — just Python and a few API keys.

**What you'll have at the end:** The full pipeline running on your machine, generating a digest, sending an email, and (optionally) publishing to GitHub Pages.

---

## Prerequisites

You need:

| Tool | Why | How to Install |
|------|-----|---------------|
| **Python 3.11+** | The language this project is written in | [python.org/downloads](https://python.org/downloads) |
| **uv** | Package manager (fast, modern, lock-file based) | [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/) |
| **Git** | To clone the repository | [git-scm.com/downloads](https://git-scm.com/downloads) |
| **API keys** (see below) | The pipeline needs these services to run | Sign up for each service below |

---

## Step 1: Sign Up for API Services

The pipeline needs 4 external services. You'll need to create accounts and get API keys for each.

### 1. Tavily Search

- **What it does:** Searches the internet for AI news
- **Sign up:** [tavily.com](https://tavily.com) → free tier gives 1,000 searches/month (this pipeline uses ~10 per run)
- **Get key:** Dashboard → API Keys → copy the key
- **You need at least 1 key** (named `TAVILY_API_KEY_1`). You can add up to 10 keys for redundancy.

### 2. DeepSeek

- **What it does:** Summarizes and ranks news stories (primary AI provider)
- **Sign up:** [platform.deepseek.com](https://platform.deepseek.com) → create account, add billing (pay-as-you-go)
- **Get key:** API Keys → create new key → copy the key
- **Cost:** ~$0.0001 per request; each daily run uses ~10 requests

### 3. Groq (Optional but Recommended)

- **What it does:** Fallback AI provider if DeepSeek is down
- **Sign up:** [console.groq.com](https://console.groq.com) → free tier gives generous rate limits
- **Get key:** API Keys → create new key → copy

### 4. Resend

- **What it does:** Sends the email digest
- **Sign up:** [resend.com](https://resend.com) → free tier gives 100 emails/day
- **Get key:** API Keys → create new key → copy
- **Important:** By default, Resend only lets the free tier send to the email address you signed up with. To send to other addresses, you need to verify a domain (under Domains in the Resend dashboard). If you haven't verified a domain, set `EMAIL_TO` to your Resend account email.

### 5. GitHub (Optional)

- **What it does:** Publishes the web edition to GitHub Pages
- **Only needed if you want the website** — the email works without it
- **Get a Personal Access Token:** GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
- **Required scopes:** `repo` (full repository access)
- If you skip this, the pipeline will run but skip the publishing step with a warning

---

## Step 2: Clone and Set Up

```bash
# Clone the repository
git clone https://github.com/exc33ded/prefect-AI-news-run.git
cd prefect-AI-news-run

# Install dependencies with uv
uv sync
```

This creates a `.venv` directory with all dependencies installed. The project uses 7 direct dependencies:

- `httpx` — HTTP client for GitHub API calls
- `jinja2` — HTML templating engine
- `openai` — OpenAI-compatible SDK (used with DeepSeek and Groq)
- `prefect` — Flow orchestration (local mode for dev)
- `python-dotenv` — Load secrets from `.env` file
- `resend` — Email delivery
- `tavily-python` — Search API client

---

## Step 3: Configure Secrets

```bash
# Copy the example environment file
cp .env.example .env
```

Now open `.env` in any text editor and fill in your API keys. Here's a complete template with explanations:

```bash
# Tavily Search API Keys (at least one required; up to 10 supported)
TAVILY_API_KEY_1=your_tavily_key_here
# TAVILY_API_KEY_2=optional_second_key
# TAVILY_API_KEY_3=optional_third_key
# ... up to TAVILY_API_KEY_10

# DeepSeek API (required — primary AI provider)
# Get from: https://platform.deepseek.com/api_keys
OPENAI_API_KEY=your_deepseek_key_here

# Groq API (optional — fallback AI provider)
# Get from: https://console.groq.com/keys
GROQ_API_KEY=your_groq_key_here

# Resend API (required — email delivery)
# Get from: https://resend.com/api-keys
RESEND_API_KEY=your_resend_key_here

# Email Settings
# The address the digest is sent FROM
EMAIL_FROM=onboarding@resend.dev

# The address the digest is sent TO
# On free Resend, this MUST be your Resend account email
EMAIL_TO=your_email@example.com

# GitHub (optional — for publishing the web edition)
# Get from: GitHub → Settings → Developer settings → Personal access tokens
GITHUB_TOKEN=your_github_pat_here

# The repository to publish to (format: owner/repo)
GITHUB_REPO=exc33ded/prefect-AI-news-run
```

**About `.env` files:** The `.env` file is gitignored — it will never be committed to the repository. Each developer has their own local `.env` with their own API keys.

**How secrets are loaded:** The `config.py` module reads from `.env` first. In Prefect Cloud, the same code reads from Prefect Secret blocks. You don't need to change any code.

---

## Step 4: Run the Pipeline

```bash
uv run python main.py
```

**What happens:**

1. The pipeline searches 10 categories of AI news simultaneously (takes ~10-20 seconds)
2. DeepSeek summarizes the results (~5-10 seconds)
3. The email is built and sent via Resend
4. The web page is rendered (and published to GitHub if configured)

**Expected output:**

```
Starting daily_ai_digest flow...
Searching: repos
Searching: skills
...
Search complete: 10/10 categories returned results
Processing results with LLM...
LLM processing complete
Rendering email...
Rendering web page...
Sending email... Done!
Publishing to GitHub Pages... Done!
Flow complete!
```

**Total runtime:** ~30-60 seconds on a typical connection.

---

## Step 5: Check the Results

### Email

Check your inbox for an email from `The AI Herald` (or `onboarding@resend.dev`). Subject line: "THE AI DAILY — [today's date]".

**If you don't see it:**
- Check your spam folder
- Free Resend tier only sends to your Resend account email — make sure `EMAIL_TO` matches
- Check the console output for "send failed" errors

### Web Edition

The output HTML is written to `docs/index.html`. Open it in your browser:

```bash
# On Windows
start docs\index.html

# On macOS
open docs/index.html

# On Linux
xdg-open docs/index.html
```

If you configured a `GITHUB_TOKEN`, the pipeline also publishes to GitHub Pages automatically.

---

## Running Just Tests

The project includes a self-test suite with 15 test functions:

```bash
uv run python test_flow.py
```

These tests verify:
- Search result parsing and normalization
- LLM fallback logic (DeepSeek → Groq → empty digest)
- Anti-hallucination (AI never writes headlines/URLs)
- GitHub repo age calculations
- Stale repo filtering (90-day threshold)
- Volume/Issue numbering

No API keys, no network — the tests are self-contained.

---

## What the Pipeline Files Do (Quick Tour)

| File | What It Does |
|------|-------------|
| `main.py` | Entry point — calls the flow |
| `daily_ai_digest/flow.py` | Orchestrates the entire pipeline (search → summarize → render → send → publish) |
| `daily_ai_digest/categories.py` | Defines the 10 search categories |
| `daily_ai_digest/search.py` | Searches Tavily for each category |
| `daily_ai_digest/process.py` | Sends search results to DeepSeek/Groq for summarization |
| `daily_ai_digest/format_email.py` | Builds the HTML email from Jinja2 template |
| `daily_ai_digest/format_page.py` | Builds the HTML web page from Jinja2 template |
| `daily_ai_digest/notify.py` | Sends the email via Resend |
| `daily_ai_digest/publish_github.py` | Publishes HTML + archive to GitHub Pages |
| `daily_ai_digest/config.py` | Loads secrets (local `.env` → env vars → Prefect blocks) |
| `daily_ai_digest/templates/` | Jinja2 HTML templates (email + edition page + archive page) |
| `test_flow.py` | 15 self-test functions |

---

## Next Steps

- **To automate this on a schedule** → go to **[Prefect Cloud Setup](../technical/backend/prefect-cloud-setup.md)**
- **To understand the code deeply** → read the **[Architecture Overview](../technical/backend/architecture-overview.md)**
- **Want to extend the pipeline?** → go to **[Extending the System](../technical/backend/extending-the-system.md)**
- **Something went wrong?** → check the **[Troubleshooting](../technical/backend/troubleshooting.md)** guide

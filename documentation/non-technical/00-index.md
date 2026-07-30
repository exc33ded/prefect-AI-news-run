# The AI Herald — Documentation

Welcome to **The AI Herald**, a fully automated daily AI news digest. Every morning at 8:00 AM IST, this pipeline searches the internet for the latest AI developments, summarizes them with AI, and delivers a vintage-newspaper-styled digest straight to your inbox and website.

This documentation will take you from "I just found this repo" to "I understand everything, can run it myself, and can extend it." You don't need any prior experience with scheduling tools, Prefect, or AI pipelines — that's what these docs are for.

## Reading Order

| # | File | What's Inside |
|---|------|--------------|
| 01 | [Understanding the Digest](01-understanding-the-digest.md) | The 10 categories, how the AI picks stories, email & website layout |
| 02 | [Getting Started (Local)](02-getting-started-local.md) | Run the full pipeline on your machine — no Prefect, no deployment |
| 03 | [FAQ](03-faq.md) | Cost, two AI providers, troubleshooting, extending |

→ **Next:** [Technical Documentation](../technical/00-index.md) — deep dives into code, deployment, and templates.

## Quick Reference

| Question | Go To |
|----------|-------|
| What is this project? | This page |
| What's in a digest? | [Understanding the Digest](01-understanding-the-digest.md) |
| How do I run it locally? | [Getting Started (Local)](02-getting-started-local.md) |
| How do I set up Prefect Cloud? | [Prefect Cloud Setup](../technical/backend/06-prefect-cloud-setup.md) |
| How do I deploy? | [Deployment Guide](../technical/backend/07-prefect-deployment-guide.md) |
| What's the architecture? | [Architecture Overview](../technical/backend/02-architecture-overview.md) |
| How do I add a new search category? | [Extending the System](../technical/backend/14-extending-the-system.md) |
| Something broke? | [Troubleshooting](../technical/backend/17-troubleshooting.md) |
| All commands in one place? | [Command Cheatsheet](../technical/backend/16-command-cheatsheet.md) |
| How does the website theme work? | [Theme System](../technical/frontend/22-theme-system.md) |

## Project at a Glance

- **Language:** Python 3.11+
- **Runs on:** Prefect Cloud (scheduled) or your laptop (manual)
- **Search:** Tavily API (10 categories, parallel execution)
- **AI Summarization:** DeepSeek (primary), Groq (fallback)
- **Email Delivery:** Resend API
- **Website:** GitHub Pages (auto-published on every run)
- **Cost:** ~$0.02 per daily run (API usage only)
- **Schedule:** Every day at 8:00 AM IST (Asia/Calcutta)
- **Published at:** [exc33ded.github.io/prefect-AI-news-run](https://exc33ded.github.io/prefect-AI-news-run/)

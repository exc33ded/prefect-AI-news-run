# Technical Documentation — Index

This is the engineering hub for The AI Herald. Everything here assumes you're comfortable with Python and want to understand, modify, deploy, or extend the system.

If you're new to the project, start with the **[Non-Technical Docs](../non-technical/00-index.md)** first.

---

## Quick File Map

```
daily_ai_digest/
├── flow.py                    ← Entry: orchestrates everything
├── categories.py              ← 10 search categories
├── config.py                  ← Secret loading (local + Prefect Cloud)
├── search.py                  ← Tavily search (parallel, with fallback keys)
├── process.py                 ← LLM summarization (DeepSeek → Groq → empty)
├── format_email.py            ← Email HTML rendering (Jinja2)
├── format_page.py             ← Web page HTML rendering (Jinja2)
├── notify.py                  ← Email sending (Resend)
├── publish_github.py          ← GitHub Pages publishing + archive
└── templates/
    ├── email.html             ← Vintage-editorial email template
    ├── edition.html           ← Gothic/parchment newspaper template
    └── archive.html           ← Calendar-grid archive template

prefect.yaml                   ← Prefect Cloud deployment config
main.py                        ← Local entrypoint
test_flow.py                   ← Self-test suite (15 tests)
pyproject.toml                 ← UV project + dependencies
requirements.txt               ← Pip-locked deps (for Prefect Cloud)
```

---

## Key Design Decisions

1. **AI Never Writes Headlines or URLs** — The LLM gets positional IDs, writes summaries only. Zero hallucination.
2. **Every Stage Is Isolated** — Search/processing/email/publishing failures don't cascade.
3. **Dual Provider Resilience** — DeepSeek (primary) → Groq (fallback) → empty digest (last resort).
4. **No Runtime Dependencies** — Everything is in the repo or in secrets. No database, no Redis.
5. **Dual Package Manager** — `uv` for local dev, `pip` for Prefect Cloud. `requirements.txt` is the bridge.
6. **Managed Work Pool (Serverless)** — Prefect provisions containers. No server management.

---

## Reading Order

Start at 00 and follow the numbers. Each page assumes you've read the ones before it.

| # | File | What's Inside |
|---|------|--------------|
| 00 | [Index](00-index.md) | This page — hub, file map, design decisions |
| 01 | [Prefect 101](01-prefect-101.md) | Prefect from scratch — concepts, `prefect.yaml` line-by-line, API keys, the full lifecycle |

### Backend

| # | File | What's Inside |
|---|------|--------------|
| 02 | [Architecture Overview](backend/02-architecture-overview.md) | System boundaries, components, data flow diagrams, patterns |
| 03 | [Project Structure](backend/03-project-structure.md) | Every file in the repo explained with code snippets |
| 04 | [Environment Setup](backend/04-environment-setup.md) | Python, uv, dependencies, IDE config |
| 05 | [API Keys & Secrets](backend/05-api-keys-and-secrets.md) | Every secret, every service, local + Prefect Cloud |
| 06 | [Prefect Cloud Setup](backend/06-prefect-cloud-setup.md) | Step-by-step: login → work pool → secrets → deploy |
| 07 | [Deployment Guide](backend/07-prefect-deployment-guide.md) | `prefect.yaml` deep dive, cron schedules, pull steps |
| 08 | [Search Pipeline](backend/08-search-pipeline.md) | 10 parallel Tavily searches, key rotation, filtering |
| 09 | [LLM Processing Pipeline](backend/09-llm-processing-pipeline.md) | DeepSeek → Groq → empty, anti-hallucination, prompt design |
| 10 | [Email Delivery](backend/10-email-delivery.md) | Resend integration, inline CSS, retry logic |
| 11 | [GitHub Pages Publishing](backend/11-github-pages-publishing.md) | Contents API, archive system, vol/issue numbering |
| 12 | [Configuration Reference](backend/12-configuration-reference.md) | Every configurable value documented |
| 13 | [Testing Guide](backend/13-testing-guide.md) | 15 test functions, adding new tests |
| 14 | [Extending the System](backend/14-extending-the-system.md) | Recipes: add category, swap LLM, change schedule |
| 15 | [Resilience & Error Handling](backend/15-resilience-and-errors.md) | Failure modes matrix, stage isolation, fail-open |
| 16 | [Command Cheatsheet](backend/16-command-cheatsheet.md) | Every CLI command: Prefect, uv, git, secrets |
| 17 | [Troubleshooting](backend/17-troubleshooting.md) | Decision tree for every problem |

### Frontend

| # | File | What's Inside |
|---|------|--------------|
| 18 | [Design System](frontend/18-design-system.md) | CSS variables, color palettes, typography, animations |
| 19 | [Edition Template](frontend/19-edition-template.md) | Website HTML structure, masthead, sections |
| 20 | [Email Template](frontend/20-email-template.md) | Email HTML, table layout, client compatibility |
| 21 | [Archive Template](frontend/21-archive-template.md) | Calendar grid, month/year selectors, modals |
| 22 | [Theme System](frontend/22-theme-system.md) | `data-theme`, CSS variables, JS toggle, localStorage |
| 23 | [Responsive Layout](frontend/23-responsive-layout.md) | 3 breakpoints, desktop/tablet/mobile behavior |
| 24 | [Jinja2 Templating](frontend/24-jinja2-templating.md) | Syntax, variable reference, PackageLoader, debugging |

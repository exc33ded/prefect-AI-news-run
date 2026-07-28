## Why

There is no automated way to stay on top of daily AI developments (new repos, agent tooling, prompting techniques, research papers) without manually checking multiple sources. A fully serverless, scheduled pipeline can search, summarize, and deliver this content daily via email and a persistent web page, with zero infrastructure to maintain.

## What Changes

- New Prefect flow (`daily_ai_digest`) deployed to Prefect Cloud on a `prefect:managed` work pool, code pulled from GitHub (no self-hosted worker).
- 4 parallel Tavily search tasks (trending AI repos, agent skills/tooling, prompting techniques, today's AI/ML papers), each biased to `time_range="day"`, with multi-key rotation/fallback across up to 4 Tavily API keys.
- One LLM processing task calling DeepSeek via the OpenAI SDK to dedupe, rank, and summarize results per category into a structured JSON schema, with retries and JSON-parse fallback.
- Two rendering tasks sharing the structured digest: a vintage-newspaper HTML email (Resend) and a "magical newspaper" GitHub Pages edition (Jinja2 template committed to `docs/`).
- One delivery task sending the email via Resend, and one publish task committing/pushing the rendered page to GitHub via the GitHub API/PAT.
- Dual dependency management: `uv` (`pyproject.toml`/`uv.lock`) for local dev, exported `requirements.txt` for Prefect Managed's pip-based install.
- All secrets (Tavily keys, DeepSeek key, Resend key, GitHub token) as Prefect Secret blocks, with local `.env` fallback via python-dotenv.
- `prefect.yaml` deployment config with daily cron schedule.

## Capabilities

### New Capabilities
- `content-search`: Parallel multi-source, multi-key Tavily search for daily AI content across 4 categories with graceful empty-result handling.
- `digest-processing`: LLM-based dedup/rank/summarize of raw search results into a structured per-category JSON digest, with retry and fallback parsing.
- `digest-formatting`: Rendering the structured digest into a newspaper-style HTML email and a separate "magical newspaper" GitHub Pages edition from shared data.
- `digest-delivery`: Sending the rendered email via Resend and publishing the rendered page to GitHub Pages via git push, each independently fault-tolerant.
- `digest-orchestration`: The top-level Prefect flow wiring search → process → format → deliver, with partial-failure tolerance and Prefect Cloud logging.

### Modified Capabilities
(none — greenfield project)

## Impact

- New standalone repo/project, package layout: `daily_ai_digest/{config,search,process,format_email,format_page,notify,publish_github,flow}.py` + `daily_ai_digest/templates/`, root-level `main.py` (local entrypoint), `test_flow.py` (self-check), `prefect.yaml`, `pyproject.toml`, `uv.lock`, `requirements.txt`, `.env.example`, `README.md`.
- External dependencies: Tavily API, DeepSeek (OpenAI-compatible API), Resend, GitHub (repo write access + Pages), Prefect Cloud (Managed work pool).
- No existing code affected (new project).

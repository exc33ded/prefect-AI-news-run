## 1. Project scaffolding

- [x] 1.1 Init `uv` project: `pyproject.toml` (Python 3.11+), deps: `prefect`, `openai`, `tavily-python` (or `httpx` if calling REST directly), `jinja2`, `resend`, `python-dotenv`, `httpx`
- [x] 1.2 Run `uv lock` to generate `uv.lock`
- [x] 1.3 Export `requirements.txt` via `uv export --frozen --no-dev --no-editable > requirements.txt`
- [x] 1.4 Create `.env.example` listing `TAVILY_API_KEY_1..4`, `OPENAI_API_KEY`, `RESEND_API_KEY`, `GITHUB_TOKEN`, `GITHUB_REPO`, `EMAIL_FROM`, `EMAIL_TO`
- [x] 1.5 Add `.gitignore` covering `.env`, `__pycache__/`, `.venv/`
- [x] 1.6 Create `config.py` (or module) with `get_secret(name)` helper: checks `.env`/`os.environ` first, falls back to `Secret.load(name).get()` on Prefect Cloud

## 2. Search stage (search.py)

- [x] 2.0 Move category definitions (key, label, query) into `categories.py` as a config list instead of one function per category, so adding categories needs no code change
- [x] 2.1 Implement Tavily key rotation helper: round-robin index across configured keys, retry-next-key on 429
- [x] 2.2 Implement generic `search_category(query, key_index)` task (Tavily, `time_range="day"`) driven by `categories.py`
- [x] 2.3 Implement `submit_all_searches()` that submits one task per configured category
- [x] 2.6 Normalize each task's output to `{title, url, snippet, published_date}` list; return `[]` on empty/error instead of raising

## 3. Processing stage (process.py)

- [x] 3.1 Define JSON schema for digest: `{category: [{title, summary, url, source_name}]}`
- [x] 3.2 Write DeepSeek prompt: dedupe near-identical, rank by relevance/novelty, top 4-6 per category, request JSON-only output
- [x] 3.3 Implement `process_results` task using OpenAI SDK, `base_url="https://api.deepseek.com"`, `model="deepseek-v4-flash"`, low `reasoning_effort`
- [x] 3.4 Add `retries=2` with exponential backoff on the task
- [x] 3.5 Implement JSON parse + one-shot "return valid JSON only" retry on parse failure; return empty digest as last resort

## 4. Formatting stage

- [x] 4.1 Create `templates/email.html`: vintage-editorial inline-CSS template (masthead, dateline, disclaimer, section dividers, headline-links-to-source, "Read today's full edition" link)
- [x] 4.2 Create `templates/edition.html`: gothic/parchment Jinja2 template with `{{REPOS_SECTION}}`/`{{SKILLS_SECTION}}`/`{{PROMPTING_SECTION}}`/`{{PAPERS_SECTION}}`/`{{DATE}}`-equivalent Jinja blocks
- [x] 4.3 Implement `format_email.py`: renders `templates/email.html` from the structured digest
- [x] 4.4 Implement `format_page.py`: renders `templates/edition.html` from the same structured digest

## 5. Delivery stage

- [x] 5.1 Implement `notify.py`: send rendered email via Resend SDK/REST, `RESEND_API_KEY` secret, configurable from/to, default sender `onboarding@resend.dev`, `retries=2`
- [x] 5.2 Implement `publish_github.py`: GitHub Contents API create-or-update for `docs/index.html` and `docs/YYYY-MM-DD.html` (fetch current `sha` first), `GITHUB_TOKEN` secret

## 6. Flow orchestration (flow.py)

- [x] 6.1 Implement `daily_ai_digest` flow: submit 4 search tasks in parallel, `.result()` each with per-task try/except (log + treat as empty on failure)
- [x] 6.2 Wire combined results into `process_results`
- [x] 6.3 Render both outputs from the same digest object
- [x] 6.4 Call `notify.send_email` and `publish_github.publish_page` independently (each wrapped so one failing doesn't block the other)
- [x] 6.5 Enable `log_prints=True`; add stage-progress log lines

## 7. Deployment

- [x] 7.1 Write `prefect.yaml`: `git_clone` (repo `exc33ded/prefect-AI-news-run`) + `pip_install_requirements` pull steps, `prefect:managed` work pool, entrypoint `flow.py:daily_ai_digest`, cron `0 7 * * *` with `timezone: Asia/Calcutta`
- [x] 7.2 Document CLI steps: `prefect work-pool create <name> --type prefect:managed`, `prefect secret create/block create` commands for each of the 6 secrets

## 8. Documentation (README.md)

- [x] 8.1 Document dual dependency workflow (`uv add` → re-export `requirements.txt` before deploy)
- [x] 8.2 Document local testing: `uv run` with `.env` populated
- [x] 8.3 Document Prefect Cloud setup: workspace, managed work pool, all Secret blocks (exact CLI), GitHub repo connection, `prefect deploy`
- [x] 8.4 Document one-time GitHub Pages setup (Settings → Pages → serve from `/docs` on `main`)
- [x] 8.5 Note GitHub Actions Secrets are NOT used (flow doesn't run in Actions); all runtime secrets are Prefect Secret blocks
- [x] 8.6 Note the DeepSeek model/base_url assumption (`deepseek-v4-flash`, `https://api.deepseek.com`) as a stated default

## 9. Verification

- [x] 9.1 `uv run python flow.py` locally with `.env` populated — confirm digest, email render, page render all produce non-empty output
- [x] 9.2 Confirm partial-failure path: stub one search task to raise, confirm flow still completes and other 3 categories populate the digest
- [x] 9.3 Confirm JSON-parse-fallback path with a forced malformed LLM response
- [x] 9.4 Deploy via `prefect deploy`, trigger one manual Prefect Cloud run, verify email received and `docs/index.html` updated on GitHub

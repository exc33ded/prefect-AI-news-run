## Context

Greenfield project, no existing code. Runs entirely on Prefect Cloud's `prefect:managed` work pool — no self-hosted worker, no server to maintain. Code is pulled from a GitHub repo at run time; the same repo's `docs/` folder is also the GitHub Pages publish target. Local dev uses `uv`; the Managed pool installs deps via pip only.

## Goals / Non-Goals

**Goals:**
- Fully serverless daily flow: search → summarize → format (email + page) → deliver, hands-off after initial setup.
- Tolerate partial failures (one search source, or one delivery channel) without failing the whole run.
- Keep local dev (`uv run`) and cloud deployment (pip/Managed) both first-class via the dual dependency files.

**Non-Goals:**
- No self-hosted worker/agent, no Docker image build, no database/state store beyond what's committed to `docs/`.
- No user-facing UI beyond the email and the static GitHub Pages HTML.
- No retry/alerting infrastructure beyond Prefect's built-in task retries and Cloud UI logging.

## Decisions

- **Managed pool dependency install → `pip_install_requirements` pull step, not `job_variables.pip_packages`.** Confirmed via Prefect docs both exist; since we already maintain an exported, locked `requirements.txt`, referencing it directly in `prefect.yaml`'s `pull` steps (after `git_clone`) keeps one source of truth instead of duplicating a package list in two places. `prefect.yaml`:
  ```yaml
  pull:
    - prefect.deployments.steps.git_clone:
        id: clone-step
        repository: <repo-url>
        branch: main
    - prefect.deployments.steps.pip_install_requirements:
        directory: "{{ clone-step.directory }}"
        requirements_file: requirements.txt
  ```

- **DeepSeek model = `deepseek-v4-flash`, base_url = `https://api.deepseek.com`.** Verified via DeepSeek's docs (Context7): `deepseek-v4-pro`/`deepseek-v4-flash` are current; legacy `deepseek-chat`/`deepseek-reasoner` names are being retired 2026-07-24. `deepseek-v4-flash` is the low-latency tier, matching the "minimal/low reasoning effort" ask. `reasoning_effort` is a real, supported param (values like `"high"`; we'll pass a low value, e.g. `"low"` or omit `thinking` entirely) — call via OpenAI SDK with `extra_body` if a field isn't natively supported by the SDK's typed params. Assumption flagged in README since the user said "v4" without a fixed model id.

- **The two outputs share the *data model*, not a template.** The prompt's "one shared template approach" header conflicts with two genuinely different aesthetics (vintage editorial email vs. gothic parchment page) and incompatible CSS rules (inline-only for email clients vs. free CSS for the page). Resolution: `process.py` produces one structured JSON digest (`{category: [{title, summary, url, source_name}]}`); `format_email.py` and `format_page.py` are two independent Jinja2 templates consuming that same object. This is the "shared" part — not markup reuse.

- **GitHub publish via the Contents API, not `git` CLI.** The Managed container is a fresh git checkout per run with no persisted git credentials/identity; shelling out to `git commit && git push` would need to configure a git identity and remote auth inline. `PUT /repos/{owner}/{repo}/contents/{path}` with the PAT (`Authorization: Bearer <GITHUB_TOKEN>`) needs only `requests`/`httpx`, handles create-or-update via the file's current `sha`, and needs two calls when writing both `docs/index.html` and `docs/YYYY-MM-DD.html` (each is a separate path/commit). `publish_github.py` fetches each target's current `sha` (404 → new file) before each `PUT`.

- **Tavily key rotation = round-robin per task index with fallback-on-429.** 4 search tasks map to keys 1–4 by fixed index (task N uses `TAVILY_API_KEY_(N mod num_keys)+1`); on a 429/rate-limit response, retry once against the next key in the list before giving up and returning an empty result for that category. Keeps the helper trivial (list + index), no shared rate-limit state needed across tasks since each search task only needs one working key per run.

- **JSON fallback parsing = one retry with a stricter reminder prompt.** If `json.loads` on the LLM response fails, re-call the same task once with an appended "Return ONLY valid JSON, no prose" instruction; if that also fails, return an empty digest for that run rather than crashing the flow (email/page still send with whatever categories parsed).

- **Secrets access = Prefect `Secret.load()` on Cloud, `os.getenv` via python-dotenv locally**, chosen by a single `get_secret(name)` helper that tries `.env`/`os.environ` first (so local dev never needs Prefect blocks configured) and falls back to `Secret.load(name).get()`.

## Confirmed Defaults

- GitHub repo: this repo's existing `origin`, `exc33ded/prefect-AI-news-run` (code source and Pages `docs/` target are the same repo).
- Schedule: daily at 08:00 `Asia/Calcutta` (IST) — expressed in `prefect.yaml` as cron `0 8 * * *` with `timezone: Asia/Calcutta`.
- Email sender: Resend test address `onboarding@resend.dev` (no verified custom domain yet).
- DeepSeek model: `deepseek-v4-flash` confirmed; `reasoning_effort`/`thinking` omitted entirely (DeepSeek docs: `low`/`medium` map to `high`, thinking defaults on — passing it would add cost/latency, not reduce it).
- Layout: package-style, not flat files — all modules live under `daily_ai_digest/` (with `daily_ai_digest/templates/`), imported via absolute imports (`from daily_ai_digest.x import y`, not relative), with a thin root-level `main.py` as the local entrypoint and `prefect.yaml`'s deployment entrypoint set to `daily_ai_digest/flow.py:daily_ai_digest`.

## Risks / Trade-offs

- [Tavily `time_range="day"` may not exist for all query types] → confirm actual param name against Tavily's current API at implementation time; fall back to filtering client-side by `published_date` if the param is missing.
- [DeepSeek JSON mode / structured output support varies] → use prompt-enforced JSON + the retry-on-parse-failure above rather than relying solely on an API-level `response_format` guarantee.
- [GitHub Contents API commit-per-file is not atomic across `index.html` + dated archive] → acceptable for a daily digest (worst case: archive updates, index doesn't, or vice versa, self-heals the following day); note in README.
- [Managed pool cannot use a custom Docker image] → all deps must be pip-installable pure-Python (Jinja2, httpx/requests, openai, resend, prefect) — no compiled/system-level dependencies; noted as a Managed-pool constraint in README.

## Migration Plan

N/A — new project, no existing deployment to migrate from. Initial rollout is manual: create Prefect Cloud workspace/work pool/Secret blocks, connect GitHub repo, `prefect deploy`, verify one manual flow run, then let the cron schedule take over.

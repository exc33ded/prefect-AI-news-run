# Deployment Guide

How the Prefect deployment works — what `prefect.yaml` contains, what happens when you deploy, and how to modify the deployment.

---

## Understanding `prefect.yaml`

This file is the single source of truth for the Prefect Cloud deployment. Here's the full file with annotations:

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/PrefectHQ/prefect/main/src/prefect/deployments/schemas/deployment.yaml

# ── Deployment Definition ──
deployments:
  - name: daily-ai-digest              # Deployment name (used in prefect deployment run)
    description: null

    # ── Entrypoint ──
    # Format: path/to/file.py:function_name
    entrypoint: daily_ai_digest/flow.py:daily_ai_digest

    # ── Parameters ──
    # Arguments passed to the flow function. None here = no args.
    parameters: {}

    # ── Work Pool ──
    work_pool:
      name: ai-digest-managed-pool     # Where the flow runs
      work_queue_name: default         # Which queue within the pool
      job_variables: {}                # Custom container settings (unused)

    # ── Schedule ──
    schedules:
      - cron: "0 8 * * *"              # Every day at 8:00 AM
        timezone: "Asia/Calcutta"      # Indian Standard Time (IST)
        day_or: true                   # Logical OR for day-of-month/month
        active: true                   # Schedule is active

    # ── Pull Steps (Environment Setup) ──
    pull:
      # Step 1: Clone the repository
      - prefect.deployments.steps.git_clone:
          repository: https://github.com/exc33ded/prefect-AI-news-run.git
          branch: main
          access_token: null           # Public repo = no token needed

      # Step 2: Install dependencies
      - prefect.deployments.steps.pip_install_requirements:
          directory: "{{ git_clone.directory }}"  # Directory from step 1
          requirements_file: requirements.txt
          pip_version: ""              # Use pip version from image

    # ── Enforcement ──
    enforce_parameter_schema: true     # Validate flow parameters
```

---

## Cron Schedule Explained

```yaml
schedules:
  - cron: "0 8 * * *"
    timezone: "Asia/Calcutta"
```

**Cron format:** `minute hour day_of_month month day_of_week`

| Field | Value | Meaning |
|-------|-------|---------|
| minute | `0` | At minute 0 |
| hour | `8` | At hour 8 (8:00 AM) |
| day_of_month | `*` | Every day |
| month | `*` | Every month |
| day_of_week | `*` | Every day of the week |

**Common alternatives:**

```yaml
# Every weekday at 9:00 AM
- cron: "0 9 * * 1-5"
  timezone: "America/New_York"

# Every Sunday at midnight
- cron: "0 0 * * 0"
  timezone: "UTC"

# Every 6 hours
- cron: "0 */6 * * *"
  timezone: "UTC"

# Twice a day (8 AM and 8 PM)
- cron: "0 8,20 * * *"
  timezone: "Asia/Calcutta"
```

---

## Pull Steps Explained

### Git Clone

```yaml
- prefect.deployments.steps.git_clone:
    repository: https://github.com/username/repo.git
    branch: main
    access_token: null
```

**What happens:** Prefect clones the specified repository at the specified branch into a temporary directory inside the container. The directory path is stored in the `{{ git_clone.directory }}` variable for subsequent steps.

**Token:** Set to `null` for public repos. For private repos, provide a GitHub token (or use a Prefect Secret block reference).

### Pip Install

```yaml
- prefect.deployments.steps.pip_install_requirements:
    directory: "{{ git_clone.directory }}"
    requirements_file: requirements.txt
```

**What happens:** Pip installs all dependencies from `requirements.txt`. The `directory` variable is populated by the previous `git_clone` step — it points to the cloned repo.

**Why pip, not uv?** Prefect managed pools use standard Python images that have pip but not uv. If/when Prefect adds uv support, switch to that.

---

## The Deploy Command

```bash
prefect deploy --name daily-ai-digest
```

**What this does:**

1. Reads `prefect.yaml` — finds all deployment definitions
2. Matches `--name daily-ai-digest` to the deployment definition
3. Reads the entrypoint file (`daily_ai_digest/flow.py`) to validate the flow exists
4. Registers the deployment in Prefect Cloud:
   - Flow metadata (name, parameters)
   - Schedule (cron + timezone)
   - Work pool + queue
   - Pull steps
5. Returns the deployment ID

**The deployment is now live.** The schedule is active immediately.

**Checking the deployment:**

```bash
prefect deployment ls
# Shows all deployments in the current workspace

prefect deployment inspect "daily-ai-digest/daily-ai-digest"
# Shows full deployment details in JSON/YAML
```

---

## Deployment Lifecycle

```
┌─────────────┐     ┌───────────────┐     ┌──────────────┐
│  CODE PUSH   │────▶│  prefect deploy│────▶│  PREFTECT    │
│  (GitHub)    │     │  (CLI)         │     │  CLOUD       │
└─────────────┘     └───────────────┘     └──────┬───────┘
                                                 │
                      ┌──────────────────────────┘
                      ▼
               ┌──────────────┐
               │  SCHEDULE     │
               │  FIRES        │
               └──────┬───────┘
                      ▼
               ┌──────────────┐
               │  WORK POOL    │
               │  PROVISIONS   │
               │  CONTAINER    │
               └──────┬───────┘
                      ▼
               ┌──────────────┐
               │  PULL STEPS   │
               │  1. git clone │
               │  2. pip inst  │
               └──────┬───────┘
                      ▼
               ┌──────────────┐
               │  FLOW RUNS    │
               └──────────────┘
```

---

## Modifying the Deployment

### Change the Schedule

Edit `prefect.yaml`:

```yaml
schedules:
  - cron: "0 6 * * *"              # Change to 6:00 AM
    timezone: "Asia/Calcutta"
    active: true
```

Then re-deploy:

```bash
prefect deploy --name daily-ai-digest
```

### Pause the Schedule

Edit `prefect.yaml`:

```yaml
schedules:
  - cron: "0 8 * * *"
    timezone: "Asia/Calcutta"
    active: false                   # Pause the schedule
```

Or from the Prefect Cloud UI:
1. Deployments → "daily-ai-digest"
2. Click the schedule toggle

### Change the Branch

```yaml
pull:
  - prefect.deployments.steps.git_clone:
      repository: https://github.com/user/repo.git
      branch: develop                 # Deploy from a different branch
```

### Add Environment Variables to the Container

```yaml
work_pool:
  name: ai-digest-managed-pool
  work_queue_name: default
  job_variables:
    env:
      MY_VAR: "value"
      ANOTHER_VAR: "another-value"
```

**Note:** Don't put secrets here. Use Prefect Secret blocks for API keys.

---

## Multiple Deployments

`prefect.yaml` can define multiple deployments. For example, a production + staging setup:

```yaml
deployments:
  # Production
  - name: daily-ai-digest
    entrypoint: daily_ai_digest/flow.py:daily_ai_digest
    work_pool:
      name: ai-digest-managed-pool
    schedules:
      - cron: "0 8 * * *"
        timezone: "Asia/Calcutta"
    pull:
      - prefect.deployments.steps.git_clone:
          repository: https://github.com/user/repo.git
          branch: main
      - prefect.deployments.steps.pip_install_requirements:
          directory: "{{ git_clone.directory }}"
          requirements_file: requirements.txt

  # Staging
  - name: daily-ai-digest-staging
    entrypoint: daily_ai_digest/flow.py:daily_ai_digest
    work_pool:
      name: ai-digest-managed-pool
    schedules:
      - cron: "0 12 * * *"           # Different time
        timezone: "Asia/Calcutta"
    pull:
      - prefect.deployments.steps.git_clone:
          repository: https://github.com/user/repo.git
          branch: staging
      - prefect.deployments.steps.pip_install_requirements:
          directory: "{{ git_clone.directory }}"
          requirements_file: requirements.txt
```

**Deploy a specific deployment:**

```bash
prefect deploy --name daily-ai-digest
prefect deploy --name daily-ai-digest-staging
```

**Deploy all:**

```bash
prefect deploy --all
```

---

## Manual Runs

### From CLI

```bash
# Standard run
prefect deployment run "daily-ai-digest/daily-ai-digest"

# Run with custom parameters (if supported)
prefect deployment run "daily-ai-digest/daily-ai-digest" --param key=value

# Run and watch logs
prefect deployment run "daily-ai-digest/daily-ai-digest" --watch
```

### From UI

1. Prefect Cloud → Deployments
2. Find "daily-ai-digest"
3. Click "Run"
4. Optional: Add parameters
5. Click "Run" to confirm

### On Schedule

No action needed. The schedule runs automatically. Check:

```bash
# See all runs (past + upcoming)
prefect flow-run ls --limit 20
```

---

## Deployment Hygiene

### Clean Up Old Flow Runs

Prefect retains flow run history indefinitely on the Hobby tier:

```bash
# Delete runs older than 30 days
prefect flow-run delete --older-than 30d
```

### Update Secrets

When API keys change or expire:

```bash
# Update a specific secret
python -c "from prefect.blocks.system import Secret; Secret(value='new_key').save('tavily-api-key-1', overwrite=True)"

# The next flow run uses the new key immediately
```

### Monitor Logs

```bash
# Watch recent runs
prefect flow-run ls --limit 10

# Inspect a specific run
prefect flow-run inspect <flow-run-id>
```

Or use the Prefect Cloud UI — click any run to see full logs.

---

## Next Steps

- Understand the code → **[Architecture Overview](02-architecture-overview.md)**
- How search works → **[Search Pipeline](08-search-pipeline.md)**
- How LLM processing works → **[LLM Processing Pipeline](09-llm-processing-pipeline.md)**
- Fixing issues → **[Troubleshooting](17-troubleshooting.md)**

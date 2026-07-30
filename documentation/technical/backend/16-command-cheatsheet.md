# Command Cheatsheet

Every command you'll ever need — all in one place. Bookmark this page.

---

## Quick Reference

| Task | Command |
|------|---------|
| Run locally | `uv run python main.py` |
| Run tests | `uv run python test_flow.py` |
| Install deps | `uv sync` |
| Export requirements | `uv export --frozen --no-dev --no-editable -o requirements.txt` |
| Deploy to Prefect Cloud | `prefect deploy --name daily-ai-digest` |
| Trigger manual run | `prefect deployment run "daily-ai-digest/daily-ai-digest"` |
| Watch logs | `prefect flow-run ls --limit 10` |
| List secrets | `prefect block ls` |

---

## Local Development

### Environment

```bash
# Clone and setup
git clone https://github.com/exc33ded/prefect-AI-news-run.git
cd prefect-AI-news-run
uv sync
cp .env.example .env
# Edit .env with your API keys
```

### Running

```bash
uv run python main.py               # Run the full pipeline
uv run python test_flow.py          # Run the test suite
```

### Dependencies

```bash
uv add <package>                    # Add a dependency
uv remove <package>                 # Remove a dependency
uv lock                             # Update lockfile
uv export --frozen --no-dev --no-editable -o requirements.txt  # Export for Prefect
```

### Python

```bash
uv run python -c "from daily_ai_digest.config import get_secret; print(get_secret('TAVILY_API_KEY_1')[:10])"  # Test secret loading
uv run python -c "from daily_ai_digest.flow import daily_ai_digest; daily_ai_digest()"  # Run flow programmatically
```

---

## Prefect CLI

### Authentication

```bash
prefect cloud login                 # Log in to Prefect Cloud
prefect cloud logout                # Log out
prefect version                     # Show version and connection status
```

### Work Pools

```bash
prefect work-pool ls                           # List work pools
prefect work-pool create <name> --type prefect:managed  # Create managed pool
prefect work-pool delete <name>                # Delete a work pool
prefect work-pool inspect <name>               # Show pool details
```

### Secrets (Blocks)

```bash
prefect block ls | grep secret                 # List secret blocks
prefect block inspect secret/tavily-api-key-1  # Check a secret exists

# Create/update a secret
python -c "from prefect.blocks.system import Secret; Secret(value='your_key').save('secret-name', overwrite=True)"

# Delete a secret
prefect block delete secret/secret-name
```

### Deployments

```bash
prefect deploy --name daily-ai-digest          # Deploy/create deployment
prefect deploy --all                           # Deploy all deployments in prefect.yaml
prefect deployment ls                          # List deployments
prefect deployment inspect "daily-ai-digest/daily-ai-digest"  # Show deployment details
```

### Running

```bash
prefect deployment run "daily-ai-digest/daily-ai-digest"     # Trigger manual run
prefect deployment run "daily-ai-digest/daily-ai-digest" --watch  # Trigger and watch logs
prefect deployment run "daily-ai-digest/daily-ai-digest" --param key=value  # With params
```

### Monitoring

```bash
prefect flow-run ls --limit 10                  # Recent/upcoming runs
prefect flow-run ls --limit 20 --state FAILED   # Failed runs only
prefect flow-run inspect <flow-run-id>          # Inspect a specific run
prefect flow-run logs <flow-run-id>             # View logs for a run
prefect flow-run cancel <flow-run-id>           # Cancel a running flow
prefect flow-run delete <flow-run-id>           # Delete a run record
prefect flow-run delete --older-than 30d        # Delete old runs
```

### Troubleshooting

```bash
prefect work-pool ls                            # Is the pool READY?
prefect block ls | grep secret                  # Do all secrets exist?
prefect deployment inspect "daily-ai-digest/daily-ai-digest"  # Is the deployment active?
prefect flow-run ls --limit 5                   # What's the latest run status?
```

---

## Git

```bash
git status                                      # What's changed?
git add .                                       # Stage all changes
git commit -m "Your message"                    # Commit
git push                                        # Push to GitHub
git log --oneline -10                           # Recent commits
```

---

## Secret Management

### Local (.env)

```bash
cp .env.example .env                            # Create from template
# Edit .env with your editor
```

### Prefect Cloud (Secret blocks)

```bash
# Create each secret
python -c "from prefect.blocks.system import Secret; Secret(value='tvly-...').save('tavily-api-key-1', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='sk-...').save('openai-api-key', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='gsk_...').save('groq-api-key', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='re_...').save('resend-api-key', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='onboarding@resend.dev').save('email-from', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='you@example.com').save('email-to', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='ghp_...').save('github-token', overwrite=True)"
python -c "from prefect.blocks.system import Secret; Secret(value='owner/repo').save('github-repo', overwrite=True)"
```

### Test Secret Loading

```bash
# Local
uv run python -c "from daily_ai_digest.config import get_secret; print(bool(get_secret('TAVILY_API_KEY_1')))"

# Prefect Cloud (the block exists, can't read value via CLI)
prefect block inspect secret/tavily-api-key-1
```

---

## Deployment Workflow

### First-Time Setup

```bash
# 1. Log in
prefect cloud login

# 2. Create work pool
prefect work-pool create ai-digest-managed-pool --type prefect:managed

# 3. Push all secrets (see Secret Management section above)

# 4. Export requirements
uv export --frozen --no-dev --no-editable -o requirements.txt

# 5. Deploy
prefect deploy --name daily-ai-digest

# 6. Test
prefect deployment run "daily-ai-digest/daily-ai-digest"
```

### Update After Code Changes

```bash
git add .
git commit -m "Description of changes"
git push
uv export --frozen --no-dev --no-editable -o requirements.txt  # If deps changed
git add requirements.txt
git commit -m "Update requirements"  # If deps changed
git push  # If deps changed
prefect deploy --name daily-ai-digest
```

### Emergency Fix

```bash
# 1. Fix the code
# 2. Push + deploy (skip requirement export if deps unchanged)
git add . && git commit -m "Emergency fix" && git push
prefect deploy --name daily-ai-digest

# 3. Trigger immediate run
prefect deployment run "daily-ai-digest/daily-ai-digest"
```

---

## GitHub Pages

### Enable

1. Repository → Settings → Pages
2. Source: Deploy from a branch
3. Branch: `main` → `/docs`
4. Save

### Check Build Status

Repository → Actions → Pages build and deployment

### Force Rebuild

Push any commit (even an empty one):

```bash
git commit --allow-empty -m "Trigger Pages rebuild"
git push
```

---

## API Testing

```bash
# Test Tavily
uv run python -c "
from tavily import TavilyClient
from daily_ai_digest.config import get_secret
c = TavilyClient(api_key=get_secret('TAVILY_API_KEY_1'))
r = c.search('AI news', max_results=2)
print(f'Found {len(r[\"results\"])} results')
"

# Test DeepSeek
uv run python -c "
from openai import OpenAI
from daily_ai_digest.config import get_secret
c = OpenAI(api_key=get_secret('OPENAI_API_KEY'), base_url='https://api.deepseek.com')
r = c.chat.completions.create(model='deepseek-v4-flash', messages=[{'role':'user','content':'Say hello in one word'}])
print(r.choices[0].message.content)
"

# Test Groq
uv run python -c "
from openai import OpenAI
from daily_ai_digest.config import get_secret
c = OpenAI(api_key=get_secret('GROQ_API_KEY'), base_url='https://api.groq.com/openai/v1')
r = c.chat.completions.create(model='llama-3.3-70b-versatile', messages=[{'role':'user','content':'Say hello in one word'}])
print(r.choices[0].message.content)
"

# Test Resend
uv run python -c "
import resend
from daily_ai_digest.config import get_secret
resend.api_key = get_secret('RESEND_API_KEY')
resend.Emails.send({'from':'onboarding@resend.dev','to':[get_secret('EMAIL_TO')],'subject':'Test','text':'Hello'})
print('Sent!')
"
```

---

## Common Sequences

### "I want to run the latest code locally"

```bash
git pull
uv sync
uv run python main.py
```

### "The schedule seems broken — check everything"

```bash
prefect deployment ls                          # Is the deployment active?
prefect flow-run ls --limit 5                   # What ran recently?
prefect work-pool ls                            # Is the pool READY?
prefect block ls | grep secret                  # Secrets exist?
```

### "A manual run failed — debug it"

```bash
prefect flow-run ls --limit 5                   # Find the failed run ID
prefect flow-run logs <flow-run-id>             # View logs
prefect flow-run inspect <flow-run-id>          # Full details
```

### "I changed API keys — update everywhere"

```bash
# Update local .env (edit file manually)

# Update Prefect Cloud
python -c "from prefect.blocks.system import Secret; Secret(value='new_key').save('secret-name', overwrite=True)"

# The next run uses the new key immediately
```

# Environment Setup

How to set up a development environment for working on The AI Herald. Covers Python, uv, dependencies, and local configuration.

---

## Prerequisites

| Tool | Version | Required? | Notes |
|------|---------|-----------|-------|
| Python | 3.11+ | Yes | Specified in `.python-version` |
| uv | Latest | Yes | Modern Python package manager |
| Git | Any | Yes | For cloning and version control |

---

## Step 1: Install Python

Download from [python.org](https://python.org/downloads/) or use a version manager:

```bash
# Option A: pyenv (recommended for version management)
pyenv install 3.11
pyenv local 3.11

# Option B: Direct install
# Download from python.org and install
```

Verify:

```bash
python --version
# Python 3.11.x
```

---

## Step 2: Install uv

```bash
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify:

```bash
uv --version
# uv 0.x.x
```

---

## Step 3: Clone and Sync

```bash
git clone https://github.com/exc33ded/prefect-AI-news-run.git
cd prefect-AI-news-run
uv sync
```

This creates a `.venv` directory with all dependencies installed exactly as specified in `uv.lock`.

**What `uv sync` does:**
1. Creates a virtual environment at `.venv/`
2. Installs all dependencies from `pyproject.toml` at the exact versions in `uv.lock`
3. (If you had a `.python-version` mismatch) Creates or uses the correct Python version

---

## Step 4: Configure Secrets

```bash
cp .env.example .env
```

Edit `.env` with your actual API keys. See [API Keys & Secrets](05-api-keys-and-secrets.md) for the complete reference.

**Minimum required keys to run:**

```bash
TAVILY_API_KEY_1=your_tavily_key      # Required — search
OPENAI_API_KEY=your_deepseek_key      # Required — LLM summarization
RESEND_API_KEY=your_resend_key        # Required — email delivery
EMAIL_TO=your_email@gmail.com         # Required — where to send
```

All other keys are optional. The pipeline will run with warnings (and skip the relevant stages) if optional keys are missing.

---

## Step 5: Verify Setup

```bash
# Run the test suite (no API keys needed)
uv run python test_flow.py

# Run the full pipeline (needs API keys)
uv run python main.py
```

---

## Understanding the Dependency System

This project uses a **dual package manager** setup. Here's why and how it works:

### Local Development: uv

```bash
uv sync          # Install all deps from uv.lock
uv add httpx     # Add a new dependency
uv remove httpx  # Remove a dependency
uv run python main.py  # Run with the project's venv
```

uv is fast (written in Rust), lock-file-based, and uses the `pyproject.toml` standard. All local development happens through uv.

### Prefect Cloud: pip

Prefect managed work pools use a standard Python container that has pip but not uv. So we export a pip-compatible lockfile:

```bash
uv export --frozen --no-dev --no-editable -o requirements.txt
```

**What the flags mean:**
- `--frozen` — use exact versions from `uv.lock` (don't re-resolve)
- `--no-dev` — exclude development dependencies
- `--no-editable` — exclude editable installs (not needed in production)
- `-o requirements.txt` — output to the file Prefect Cloud reads

**The chain:**

```
pyproject.toml  ←  Declare what you need
      ↓
  uv lock       ←  Resolve exact versions + hashes
      ↓
  uv.lock       ←  Canonical lock (commit this)
      ↓
  uv export     ←  Convert to pip format
      ↓
requirements.txt ← Prefect Cloud installs from this
```

### When to Re-export

Re-export `requirements.txt` when:
- You add, remove, or update a dependency in `pyproject.toml`
- You run `uv lock` to update dependency versions

**Rule of thumb:** If `uv.lock` changed, re-export `requirements.txt`.

```bash
uv sync               # Install new deps locally
uv lock               # Update lockfile (if needed)
uv export --frozen --no-dev --no-editable -o requirements.txt  # Re-export
git add requirements.txt uv.lock pyproject.toml
git commit -m "Update dependencies"
```

---

## Local vs. Cloud Configuration

| Aspect | Local Dev | Prefect Cloud |
|--------|-----------|---------------|
| Package manager | uv | pip |
| Secret source | `.env` file | Prefect Secret blocks |
| Python version | As installed | prefecthq/prefect:3-latest image |
| Entrypoint | `uv run python main.py` | `daily_ai_digest/flow.py:daily_ai_digest` |
| Dependencies | From `uv.lock` | From `requirements.txt` |
| Network access | Your machine's network | Prefect container's network |

The same code (`config.py:get_secret()`) handles both environments transparently.

---

## IDE Setup

### VS Code

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": ".venv/Scripts/python.exe",
    "python.terminal.activateEnvironment": true,
    "[python]": {
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "ms-python.black-formatter"
    }
}
```

The `.venv` in your interpreter path ensures VS Code uses the project's virtual environment.

### PyCharm

PyCharm should auto-detect the `.venv` directory. If not:
- File → Settings → Project → Python Interpreter → Add Interpreter → Existing → `.venv/Scripts/python.exe`

---

## Common Issues

### "uv: command not found"

The uv binary isn't in your PATH. Reinstall or add the install directory to PATH:

```bash
# Check where uv installed
# Windows: %USERPROFILE%\.cargo\bin\
# macOS/Linux: ~/.cargo/bin/

# Add to PATH (add this to your shell profile)
export PATH="$HOME/.cargo/bin:$PATH"
```

### "Python version mismatch"

If `.python-version` specifies 3.11 but you have 3.12 installed:

```bash
# Install the correct version with pyenv
pyenv install 3.11

# Or change .python-version to match your installation
echo "3.12" > .python-version
uv sync  # Re-install with new version
```

### "ModuleNotFoundError: No module named 'daily_ai_digest'"

You're likely not running from the project root or not using uv:

```bash
# Wrong:
python main.py

# Right:
cd prefect-AI-news-run
uv run python main.py
```

The `uv run` command activates the virtual environment and runs the script with the correct Python path.

### ".env file not found"

Copy the template:

```bash
cp .env.example .env
```

Then edit `.env` with your actual keys. The file is gitignored, so it's private to your machine.

---

## Next Steps

- Every API key explained → **[API Keys & Secrets](05-api-keys-and-secrets.md)**
- Set up Prefect Cloud → **[Prefect Cloud Setup](06-prefect-cloud-setup.md)**
- Run the pipeline locally → **[Getting Started (Local)](../../non-technical/02-getting-started-local.md)**
- All commands in one place → **[Command Cheatsheet](16-command-cheatsheet.md)**

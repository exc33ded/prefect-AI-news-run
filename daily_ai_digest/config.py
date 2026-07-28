import os

from dotenv import load_dotenv

load_dotenv()


def get_secret(name: str) -> str:
    """Read a secret from .env/env vars locally, or a Prefect Secret block on Cloud."""
    value = os.getenv(name)
    if value:
        return value

    from prefect.blocks.system import Secret

    return Secret.load(name.lower().replace("_", "-")).get()

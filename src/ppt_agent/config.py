import contextvars
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "PPT_AGENT_", "env_file": ".env", "extra": "ignore"}

    model: str = "openai:gpt-4o"
    output_dir: Path = Path("./output")

    # Concurrency limits
    research_concurrency: int = 3
    slide_concurrency: int = 3
    render_concurrency: int = 5

    # OpenAI-compatible provider (OpenAI, DeepSeek, Qwen, Moonshot, etc.)
    openai_api_key: str = ""
    openai_base_url: str = ""

    # Anthropic-compatible provider (Anthropic, or third-party Claude endpoints)
    anthropic_api_key: str = ""
    anthropic_base_url: str = ""

    # Web search config
    search_provider: str = ""          # "tavily" | "" (disabled)
    tavily_api_key: str = ""

    # API server
    api_host: str = "0.0.0.0"
    api_port: int = 9999


settings = Settings()

# ---------------------------------------------------------------------------
# Per-session output directory — set by main.py before each agent invocation
# ---------------------------------------------------------------------------

_current_session_dir: contextvars.ContextVar[Path] = contextvars.ContextVar(
    "session_dir", default=settings.output_dir
)


def get_session_dir() -> Path:
    return _current_session_dir.get()

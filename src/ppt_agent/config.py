import contextvars
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "PPT_AGENT_", "env_file": ".env", "extra": "ignore"}

    model: str = "anthropic:claude-sonnet-4-6"
    output_dir: Path = Path("./output")

    # Concurrency limits
    research_concurrency: int = 3
    slide_concurrency: int = 3
    render_concurrency: int = 5

    # VLLM config
    vllm_base_url: str = ""
    vllm_api_key: str = "empty"

    # ZhipuAI config (OpenAI-compatible endpoint)
    zhipu_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    zhipu_api_key: str = ""

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

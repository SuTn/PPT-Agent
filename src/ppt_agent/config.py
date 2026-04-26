from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "PPT_AGENT_", "env_file": ".env", "extra": "ignore"}

    model: str = "anthropic:claude-sonnet-4-6"
    output_dir: Path = Path("./output")

    # Concurrency limits
    slide_concurrency: int = 3
    render_concurrency: int = 5

    # VLLM config
    vllm_base_url: str = ""
    vllm_api_key: str = "empty"

    # ZhipuAI config (OpenAI-compatible endpoint)
    zhipu_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    zhipu_api_key: str = ""


settings = Settings()

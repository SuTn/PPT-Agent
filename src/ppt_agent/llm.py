from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from ppt_agent.config import settings


def get_model(model: str | None = None) -> BaseChatModel:
    """Create a chat model instance.

    Supported formats:
      - "anthropic:claude-sonnet-4-6"     (uses ANTHROPIC_API_KEY)
      - "openai:gpt-4o"                   (uses OPENAI_API_KEY)
      - "openrouter:google/gemini-2.5-flash" (uses PPT_AGENT_OPENROUTER_API_KEY)
      - "vllm:Qwen/Qwen2.5-72B-Instruct" (uses PPT_AGENT_VLLM_BASE_URL + VLLM_API_KEY)
      - "zhipu:glm-4"                     (uses PPT_AGENT_ZHIPU_API_KEY + ZHIPU_BASE_URL)
    """
    model = model or settings.model

    provider, _, model_name = model.partition(":")

    if provider == "vllm":
        if not settings.vllm_base_url:
            raise ValueError("PPT_AGENT_VLLM_BASE_URL is required for vllm provider")
        return ChatOpenAI(
            model=model_name,
            base_url=settings.vllm_base_url,
            api_key=settings.vllm_api_key,
        )

    if provider == "zhipu":
        if not settings.zhipu_api_key:
            raise ValueError("PPT_AGENT_ZHIPU_API_KEY is required for zhipu provider")
        return ChatOpenAI(
            model=model_name,
            base_url=settings.zhipu_base_url,
            api_key=settings.zhipu_api_key,
        )

    if provider == "openrouter":
        if not settings.openrouter_api_key:
            raise ValueError("PPT_AGENT_OPENROUTER_API_KEY is required for openrouter provider")
        return ChatOpenAI(
            model=model_name,
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
        )

    return init_chat_model(model, temperature=0.7)

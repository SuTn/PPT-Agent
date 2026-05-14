from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from ppt_agent.config import settings


def _patch_reasoning_content():
    """Monkey-patch langchain_openai to preserve reasoning_content for thinking models.

    ChatOpenAI strips reasoning_content from API responses, but models like
    MiMo require it to be passed back on subsequent calls (especially after
    tool use). This patch preserves reasoning_content in AIMessage.additional_kwargs
    and includes it when converting back to API format.
    """
    import langchain_openai.chat_models.base as _base

    _orig_to_msg = _base._convert_dict_to_message
    _orig_to_dict = _base._convert_message_to_dict

    def _patched_to_msg(_dict):
        msg = _orig_to_msg(_dict)
        if (
            isinstance(msg, _base.AIMessage)
            and "reasoning_content" in _dict
            and _dict["reasoning_content"]
        ):
            msg.additional_kwargs["reasoning_content"] = _dict["reasoning_content"]
        return msg

    def _patched_to_dict(message, **kwargs):
        d = _orig_to_dict(message, **kwargs)
        if (
            isinstance(message, _base.AIMessage)
            and "reasoning_content" in message.additional_kwargs
        ):
            d["reasoning_content"] = message.additional_kwargs["reasoning_content"]
        return d

    _base._convert_dict_to_message = _patched_to_msg
    _base._convert_message_to_dict = _patched_to_dict


_patch_reasoning_content()


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

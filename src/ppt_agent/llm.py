from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

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


def get_model(model: str | None = None):
    """Create a chat model instance.

    Supported formats:
      - "openai:<model>"       — OpenAI-compatible (DeepSeek, Qwen, Moonshot, etc.)
      - "anthropic:<model>"    — Anthropic-compatible (Claude, or third-party endpoints)

    Both providers support custom base_url + api_key via settings.

    Examples:
      - "openai:gpt-4o"                          → OpenAI
      - "openai:deepseek-chat"                    → DeepSeek  (set OPENAI_BASE_URL)
      - "openai:qwen-plus"                        → Qwen      (set OPENAI_BASE_URL)
      - "anthropic:claude-sonnet-4-6"             → Anthropic
      - "anthropic:claude-sonnet-4-6"             → Third-party (set ANTHROPIC_BASE_URL)
    """
    model = model or settings.model

    provider, _, model_name = model.partition(":")

    if provider == "openai":
        kwargs = {"model": model_name, "temperature": 0.7}
        if settings.openai_api_key:
            kwargs["api_key"] = settings.openai_api_key
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        return ChatOpenAI(**kwargs)

    if provider == "anthropic":
        kwargs = {"model": model_name, "temperature": 0.7}
        if settings.anthropic_api_key:
            kwargs["api_key"] = settings.anthropic_api_key
        if settings.anthropic_base_url:
            kwargs["base_url"] = settings.anthropic_base_url
        return ChatAnthropic(**kwargs)

    raise ValueError(
        f"Unknown provider: {provider!r}. Use 'openai:<model>' or 'anthropic:<model>'"
    )

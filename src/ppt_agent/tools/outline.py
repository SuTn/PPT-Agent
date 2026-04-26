import json
import re
from pathlib import Path

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from pydantic import ValidationError

from ppt_agent.agent.state import Outline, SessionState, PipelineStep
from ppt_agent.config import settings
from ppt_agent.llm import get_model
from ppt_agent.prompts.outline import OUTLINE_PROMPT


def _extract_json(text: str) -> str:
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0).strip()
    return text.strip()


def _try_parse_json(text: str) -> dict | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fixed = re.sub(r",\s*([}\]])", r"\1", text)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    fixed = text.replace("'", '"')
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    return None


_RETRY_HINT = (
    "你上一次输出的不是合法的 JSON。请严格输出纯 JSON，"
    "不要包含注释、尾逗号或其他文本。只返回 JSON 对象。"
)


def _state_path() -> Path:
    return settings.output_dir / "session.json"


@tool
def generate_outline(requirements: str, page_count: int = 10) -> str:
    """根据用户需求生成 PPT 大纲。

    在用户确认了演示主题和需求后调用此工具。生成结构化的大纲 JSON，
    包含每页的布局类型、标题和要点。

    Args:
        requirements: 用户的演示需求描述，包含主题、受众、关键内容等。
        page_count: 期望的幻灯片页数，默认 10 页。
    """
    model = get_model()
    base_prompt = OUTLINE_PROMPT.format(
        requirements=requirements,
        page_count=page_count,
    )

    last_raw = ""
    last_error = ""
    messages = [HumanMessage(content=base_prompt)]

    for attempt in range(3):
        response = model.invoke(messages)
        last_raw = _extract_json(response.content)
        raw_dict = _try_parse_json(last_raw)

        if raw_dict:
            try:
                outline = Outline.model_validate(raw_dict)
                break
            except ValidationError as e:
                last_error = str(e)

        if attempt < 2:
            hint = _RETRY_HINT
            if last_error:
                hint += f"\n具体错误：{last_error}"
            messages.append(HumanMessage(content=hint))
    else:
        return f"[错误] 大纲生成失败，尝试了 3 次。最后错误：{last_error}\n原始输出：{last_raw[:500]}"

    # persist outline
    outline_path = settings.output_dir / "outline.json"
    outline_path.parent.mkdir(parents=True, exist_ok=True)
    with open(outline_path, "w", encoding="utf-8") as f:
        json.dump(outline.model_dump(), f, ensure_ascii=False, indent=2)

    # update session state
    state = SessionState.load(_state_path())
    state.step = PipelineStep.OUTLINE_DONE
    state.title = outline.title
    state.outline_file = str(outline_path)
    state.save(_state_path())

    return json.dumps(outline.model_dump(), ensure_ascii=False, indent=2)

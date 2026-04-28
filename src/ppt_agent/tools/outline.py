import json
import re
from pathlib import Path

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from pydantic import ValidationError

from ppt_agent.agent.state import Outline, SessionState, PipelineStep, sync_session_index
from ppt_agent.config import get_session_dir, settings
from ppt_agent.llm import get_model
from ppt_agent.prompts.outline import OUTLINE_PROMPT, _materials_section, _research_section


def _extract_json(text: str) -> str:
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    start = text.find("{")
    if start == -1:
        return text.strip()
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1].strip()
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

    return None


_RETRY_HINT = (
    "你上一次输出的不是合法的 JSON。请严格输出纯 JSON，"
    "不要包含注释、尾逗号或其他文本。只返回 JSON 对象。"
)


def _state_path() -> Path:
    return get_session_dir() / "session.json"


@tool
async def generate_outline(requirements: str, page_count: int = 0, materials: str = "") -> str:
    """根据用户需求和研究笔记生成 PPT 大纲。

    在用户确认了演示主题和需求后调用此工具。生成结构化的大纲 JSON，
    包含叙事框架、Action Title、支撑论据和证据。

    Args:
        requirements: 用户的演示需求描述，包含主题、受众、关键内容等。
        page_count: 期望的幻灯片页数。0 表示根据内容复杂度自行决定（默认）。
        materials: 用户上传的参考材料内容（Markdown 格式）。如果为空，自动从会话目录的 materials.md 读取。
    """
    session_dir = get_session_dir()

    # Auto-read materials.md if not provided
    if not materials:
        materials_path = session_dir / "materials.md"
        if materials_path.exists():
            materials = materials_path.read_text(encoding="utf-8")

    # Auto-read research_notes.md
    research = ""
    research_path = session_dir / "research_notes.md"
    if research_path.exists():
        research = research_path.read_text(encoding="utf-8")

    model = get_model()
    if page_count > 0:
        page_instruction = f"- 总页数控制在 {page_count} 页左右"
    else:
        page_instruction = "- 总页数根据内容复杂度自行决定：简单主题 5-8 页，中等主题 8-15 页，复杂主题 15-25 页。确保每页信息量适中，不要为了凑页数而注水。"

    base_prompt = OUTLINE_PROMPT.format(
        requirements=requirements,
        page_instruction=page_instruction,
        materials_section=_materials_section(materials),
        research_section=_research_section(research),
    )

    last_raw = ""
    last_error = ""
    messages = [HumanMessage(content=base_prompt)]

    for attempt in range(3):
        response = await model.ainvoke(messages)
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
    outline_path = session_dir / "outline.json"
    outline_path.parent.mkdir(parents=True, exist_ok=True)
    with open(outline_path, "w", encoding="utf-8") as f:
        json.dump(outline.model_dump(), f, ensure_ascii=False, indent=2)

    # update session state
    state = SessionState.load(_state_path())
    state.step = PipelineStep.OUTLINE_DONE
    state.title = outline.title
    state.outline_file = str(outline_path)
    state.save(_state_path())
    sync_session_index(state.session_id, step=state.step.value, title=outline.title)

    return json.dumps(outline.model_dump(), ensure_ascii=False, indent=2)

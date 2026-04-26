import json
import re

from langchain_core.tools import tool

from ppt_agent.config import settings
from ppt_agent.llm import get_model
from ppt_agent.prompts.outline import OUTLINE_PROMPT


def _extract_json(text: str) -> str:
    """Extract JSON object from LLM response."""
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0).strip()
    return text.strip()


def _try_parse_json(text: str) -> dict | None:
    """Try to parse JSON, with common fixups."""
    # direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # common fix: trailing commas before } or ]
    fixed = re.sub(r",\s*([}\]])", r"\1", text)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # common fix: single quotes → double quotes
    fixed = text.replace("'", '"')
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    return None


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
    prompt = OUTLINE_PROMPT.format(
        requirements=requirements,
        page_count=page_count,
    )

    for attempt in range(3):
        response = model.invoke(prompt)
        raw = _extract_json(response.content)

        outline = _try_parse_json(raw)
        if outline and "title" in outline and "slides" in outline:
            break

        # retry with error hint
        if attempt < 2:
            prompt += f"\n\n上一次输出格式有误，请严格输出合法 JSON，不要有注释或尾逗号。重新生成："
    else:
        return f"[错误] 大纲 JSON 生成失败，尝试了 3 次无法解析。最后一次输出：\n{raw[:500]}"

    # persist
    outline_path = settings.output_dir / "outline.json"
    outline_path.parent.mkdir(parents=True, exist_ok=True)
    with open(outline_path, "w", encoding="utf-8") as f:
        json.dump(outline, f, ensure_ascii=False, indent=2)

    return json.dumps(outline, ensure_ascii=False, indent=2)

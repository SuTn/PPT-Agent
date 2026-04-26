import json
import re

from langchain_core.tools import tool

from ppt_agent.config import settings
from ppt_agent.llm import get_model
from ppt_agent.prompts.slide import SLIDE_PROMPT

_CODE_FENCE = re.compile(r"```(?:html)?\s*(.*?)\s*```", re.DOTALL)


def _strip_code_fence(text: str) -> str:
    match = _CODE_FENCE.search(text)
    if match:
        return match.group(1).strip()
    return text.strip()


@tool
def generate_slides(outline: str, style_spec: str) -> str:
    """根据大纲和风格规范逐页生成 HTML 幻灯片。

    Args:
        outline: 大纲 JSON 字符串，由 generate_outline 生成。
        style_spec: 风格规范 JSON 字符串，由 select_template 返回。
    """
    outline_data = json.loads(outline)
    slides = outline_data["slides"]
    total = len(slides)

    model = get_model()
    slides_dir = settings.output_dir / "slides"
    slides_dir.mkdir(parents=True, exist_ok=True)

    generated = []
    for i, slide_info in enumerate(slides):
        prompt = SLIDE_PROMPT.format(
            page=slide_info["page"],
            total=total,
            layout=slide_info["layout"],
            title=slide_info["title"],
            key_points=json.dumps(slide_info.get("key_points", []), ensure_ascii=False),
            style_spec=style_spec,
        )

        response = model.invoke(prompt)
        html_content = _strip_code_fence(response.content)

        filename = f"slide_{slide_info['page']:02d}_{slide_info['layout']}.html"
        filepath = slides_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        generated.append(str(filepath))

    return f"已生成 {len(generated)} 张幻灯片:\n" + "\n".join(generated)

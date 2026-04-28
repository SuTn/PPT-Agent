import asyncio
import json
import re

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

from ppt_agent.agent.state import SessionState, PipelineStep
from ppt_agent.config import get_session_dir, settings
from ppt_agent.llm import get_model
from ppt_agent.prompts.slide import SLIDE_PROMPT
from ppt_agent.templates.registry import load_skeleton, render_skeleton

_CODE_FENCE = re.compile(r"```(?:html)?\s*(.*?)\s*```", re.DOTALL)


def _strip_code_fence(text: str) -> str:
    match = _CODE_FENCE.search(text)
    if match:
        return match.group(1).strip()
    return text.strip()


def _is_valid_html(text: str) -> bool:
    lower = text.lower()
    return "<html" in lower or "<body" in lower or "<div" in lower


async def _generate_one_slide(
    sem: asyncio.Semaphore,
    model,
    slide_info: dict,
    total: int,
    style_spec: dict,
    template_key: str,
) -> tuple[dict, str]:
    async with sem:
        layout = slide_info["layout"]
        headline = slide_info.get("headline", "")
        page = slide_info["page"]

        # Load skeleton for this layout
        skeleton = load_skeleton(layout, template_key)

        # Generate content area HTML via LLM
        prompt = SLIDE_PROMPT.format(
            page=page,
            total=total,
            layout=layout,
            headline=headline,
            body_text=slide_info.get("body_text", ""),
            supporting_points=json.dumps(
                slide_info.get("supporting_points", []), ensure_ascii=False
            ),
            speaker_notes=slide_info.get("speaker_notes", ""),
            section=slide_info.get("section", ""),
            visual_hint=slide_info.get("visual_hint", ""),
        )
        response = await model.ainvoke([HumanMessage(content=prompt)])
        content_html = _strip_code_fence(response.content)

        # Merge into skeleton
        full_html = render_skeleton(
            skeleton_html=skeleton,
            style_spec=style_spec,
            headline=headline,
            page=page,
            total=total,
            content=content_html,
            speaker_notes=slide_info.get("speaker_notes", ""),
        )

        return slide_info, full_html


@tool
async def generate_slides() -> str:
    """根据大纲和风格规范并发生成所有 HTML 幻灯片。

    自动读取 outline.json 和 style_spec.json，并发调用 LLM 生成每页 HTML。
    """
    session_dir = get_session_dir()
    outline_path = session_dir / "outline.json"
    style_spec_path = session_dir / "style_spec.json"

    if not outline_path.exists():
        return "[错误] outline.json 不存在，请先生成大纲。"
    if not style_spec_path.exists():
        return "[错误] style_spec.json 不存在，请先选择模板。"

    with open(outline_path, "r", encoding="utf-8") as f:
        outline = json.load(f)
    with open(style_spec_path, "r", encoding="utf-8") as f:
        style_spec = json.load(f)

    # Load template_key from session state
    state = SessionState.load(session_dir / "session.json")
    template_key = state.template_key or ""

    slides = outline["slides"]
    total = len(slides)
    model = get_model()
    sem = asyncio.Semaphore(settings.slide_concurrency)

    slides_dir = session_dir / "slides"
    slides_dir.mkdir(parents=True, exist_ok=True)

    tasks = [
        _generate_one_slide(sem, model, s, total, style_spec, template_key)
        for s in slides
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    generated = []
    failed = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            failed.append(f"第 {slides[i]['page']} 页: {result}")
            continue
        slide_info, html_content = result
        if not html_content or not _is_valid_html(html_content):
            failed.append(f"第 {slide_info['page']} 页: 生成的 HTML 内容无效")
            continue
        filename = f"slide_{slide_info['page']:02d}_{slide_info['layout']}.html"
        filepath = slides_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        generated.append(str(filepath))

    state = SessionState.load(session_dir / "session.json")
    state.step = PipelineStep.SLIDES_DONE
    state.slides_dir = str(slides_dir)
    state.save(session_dir / "session.json")

    msg = f"已生成 {len(generated)} 张幻灯片:\n" + "\n".join(generated)
    if failed:
        msg += f"\n\n[警告] {len(failed)} 张幻灯片生成失败:\n" + "\n".join(failed)
    return msg

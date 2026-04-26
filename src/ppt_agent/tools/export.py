import asyncio
import glob
import uuid
from pathlib import Path

from langchain_core.tools import tool

from ppt_agent.agent.state import SessionState, PipelineStep
from ppt_agent.config import settings
from ppt_agent.export.renderer import browser_context, render_html_to_png
from ppt_agent.export.pptx_builder import build_pptx


@tool
async def export_pptx(slides_dir: str = "") -> str:
    """将生成的 HTML 幻灯片转换为 PPTX 文件。

    Args:
        slides_dir: 幻灯片 HTML 文件所在目录。默认使用 output/slides。
    """
    if not slides_dir:
        slides_dir = str(settings.output_dir / "slides")

    html_files = sorted(glob.glob(str(Path(slides_dir) / "*.html")))
    if not html_files:
        return f"未找到 HTML 文件: {slides_dir}"

    pptx_dir = settings.output_dir / "pptx"
    pptx_dir.mkdir(parents=True, exist_ok=True)
    pptx_path = pptx_dir / f"presentation_{uuid.uuid4().hex[:8]}.pptx"

    sem = asyncio.Semaphore(settings.render_concurrency)

    async def _render_one(html_path: str) -> str:
        async with sem:
            png_path = html_path.replace(".html", ".png")
            await render_html_to_png(html_path, png_path, browser)
            return png_path

    async with browser_context() as browser:
        pngs = await asyncio.gather(*[_render_one(f) for f in html_files])

    build_pptx(sorted(pngs), pptx_path)

    # update session state
    state = SessionState.load(settings.output_dir / "session.json")
    state.step = PipelineStep.EXPORTED
    state.pptx_file = str(pptx_path)
    state.save(settings.output_dir / "session.json")

    return f"PPTX 已导出: {pptx_path}"

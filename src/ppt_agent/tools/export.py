import asyncio
import glob
from pathlib import Path

from langchain_core.tools import tool

from ppt_agent.agent.state import SessionState, PipelineStep, sync_session_index
from ppt_agent.config import get_session_dir, settings
from ppt_agent.export.renderer import browser_context, render_html_to_png
from ppt_agent.export.pptx_builder import build_pptx


async def do_export(session_dir: Path) -> str:
    """Core export logic: HTML slides → PNG → PPTX."""
    slides_dir = session_dir / "slides"
    if not slides_dir.exists():
        return f"未找到幻灯片目录: {slides_dir}"

    html_files = sorted(glob.glob(str(slides_dir / "*.html")))
    if not html_files:
        return f"未找到 HTML 文件: {slides_dir}"

    state = SessionState.load(session_dir / "session.json")
    filename = (state.title or state.session_id).replace("/", "_").replace(" ", "_")
    pptx_path = session_dir / f"{filename}.pptx"

    sem = asyncio.Semaphore(settings.render_concurrency)

    async def _render_one(html_path: str, browser) -> str:
        async with sem:
            png_path = html_path.replace(".html", ".png")
            await render_html_to_png(html_path, png_path, browser)
            return png_path

    async with browser_context() as browser:
        render_results = await asyncio.gather(
            *[_render_one(f, browser) for f in html_files],
            return_exceptions=True,
        )

    pngs = []
    render_failed = []
    for i, r in enumerate(render_results):
        if isinstance(r, Exception):
            render_failed.append(f"{Path(html_files[i]).name}: {r}")
        else:
            pngs.append(r)

    build_failed = build_pptx(sorted(pngs), pptx_path)

    state.step = PipelineStep.EXPORTED
    state.pptx_file = str(pptx_path)
    state.save(session_dir / "session.json")
    sync_session_index(state.session_id, step=state.step.value)

    msg = f"PPTX 已导出: {pptx_path}"
    if render_failed:
        msg += f"\n\n[警告] {len(render_failed)} 张幻灯片渲染失败:\n" + "\n".join(render_failed)
    if build_failed:
        msg += f"\n\n[警告] {len(build_failed)} 张幻灯片嵌入失败（PNG 损坏）"
    return msg


@tool
async def export_pptx(slides_dir: str = "") -> str:
    """将生成的 HTML 幻灯片转换为 PPTX 文件。

    Args:
        slides_dir: 幻灯片 HTML 文件所在目录。默认使用当前会话的 slides/ 目录。
    """
    session_dir = get_session_dir()
    return await do_export(session_dir)

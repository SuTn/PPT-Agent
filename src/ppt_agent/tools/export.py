import asyncio
import glob
import uuid
from pathlib import Path

from langchain_core.tools import tool

from ppt_agent.config import settings
from ppt_agent.export.renderer import render_html_to_png
from ppt_agent.export.pptx_builder import build_pptx


@tool
def export_pptx(slides_dir: str = "") -> str:
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

    pngs = asyncio.run(_render_all(html_files))
    build_pptx(pngs, pptx_path)

    return f"PPTX 已导出: {pptx_path}"


async def _render_all(html_files: list[str]) -> list[str]:
    pngs = []
    for html_path in html_files:
        png_path = html_path.replace(".html", ".png")
        await render_html_to_png(html_path, png_path)
        pngs.append(png_path)
    return pngs

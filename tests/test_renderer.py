"""Test HTML rendering and PPTX export pipeline."""

import asyncio
from pathlib import Path

import pytest

from ppt_agent.export.renderer import render_html_to_png
from ppt_agent.export.pptx_builder import build_pptx


SAMPLE_HTML = """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  width: 1280px; height: 720px; overflow: hidden;
  font-family: 'Microsoft YaHei', sans-serif;
  background: #ffffff;
  display: flex; align-items: center; justify-content: center;
}
h1 { font-size: 48px; color: #1a365d; }
</style>
</head>
<body><h1>PPT-Agent Test Slide</h1></body>
</html>"""


@pytest.fixture
def tmp_files(tmp_path):
    html_path = tmp_path / "test.html"
    png_path = tmp_path / "test.png"
    pptx_path = tmp_path / "test.pptx"
    html_path.write_text(SAMPLE_HTML, encoding="utf-8")
    return html_path, png_path, pptx_path


@pytest.mark.asyncio
async def test_render_html(tmp_files):
    html_path, png_path, pptx_path = tmp_files
    await render_html_to_png(str(html_path), str(png_path))
    assert png_path.exists()
    assert png_path.stat().st_size > 1000


@pytest.mark.asyncio
async def test_build_pptx(tmp_files):
    html_path, png_path, pptx_path = tmp_files
    await render_html_to_png(str(html_path), str(png_path))
    build_pptx([str(png_path)], pptx_path)
    assert pptx_path.exists()
    assert pptx_path.stat().st_size > 10000

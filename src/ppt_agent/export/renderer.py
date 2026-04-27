import asyncio
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from playwright.sync_api import Browser, sync_playwright

_thread_local = threading.local()


def _get_or_create_browser() -> Browser:
    if not hasattr(_thread_local, "pw"):
        _thread_local.pw = sync_playwright().start()
        _thread_local.browser = _thread_local.pw.chromium.launch()
    return _thread_local.browser


def _close_browser() -> None:
    if hasattr(_thread_local, "pw"):
        try:
            _thread_local.browser.close()
            _thread_local.pw.stop()
        except Exception:
            pass
        del _thread_local.pw
        if hasattr(_thread_local, "browser"):
            del _thread_local.browser


def _render_sync(html_path: str, output_path: str) -> None:
    browser = _get_or_create_browser()
    page = browser.new_page(
        viewport={"width": 1280, "height": 720},
        device_scale_factor=2,
    )
    try:
        page.goto(f"file:///{Path(html_path).absolute().as_posix()}")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=output_path, full_page=False)
    finally:
        page.close()


async def render_html_to_png(html_path: str, output_path: str, browser=None) -> None:
    await asyncio.to_thread(_render_sync, html_path, output_path)


@asynccontextmanager
async def browser_context():
    """Compatibility shim — callers still use `async with browser_context() as browser`."""
    await asyncio.to_thread(_get_or_create_browser)
    try:
        yield None
    finally:
        await asyncio.to_thread(_close_browser)

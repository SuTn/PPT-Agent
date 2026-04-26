from contextlib import asynccontextmanager
from pathlib import Path

from playwright.async_api import Browser, async_playwright


@asynccontextmanager
async def browser_context():
    """Launch a single browser instance for reuse across multiple screenshots."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        try:
            yield browser
        finally:
            await browser.close()


async def render_html_to_png(
    html_path: str, output_path: str, browser: Browser
) -> None:
    page = await browser.new_page(
        viewport={"width": 1280, "height": 720},
        device_scale_factor=2,
    )
    try:
        await page.goto(f"file:///{Path(html_path).absolute().as_posix()}")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=output_path, full_page=False)
    finally:
        await page.close()

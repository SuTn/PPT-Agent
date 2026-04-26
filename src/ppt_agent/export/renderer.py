from pathlib import Path

from playwright.async_api import async_playwright


async def render_html_to_png(html_path: str, output_path: str) -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(
            viewport={"width": 1280, "height": 720},
            device_scale_factor=2,
        )
        await page.goto(f"file:///{Path(html_path).absolute().as_posix()}")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=output_path, full_page=False)
        await browser.close()

from __future__ import annotations

import asyncio
import logging

from playwright.async_api import Browser, Playwright, async_playwright

from src.config.constants import SLIDE_HEIGHT, SLIDE_WIDTH

logger = logging.getLogger(__name__)

_playwright: Playwright | None = None
_browser: Browser | None = None
_lock = asyncio.Lock()


async def _ensure_browser() -> Browser:
    """Lazily start Playwright and launch headless Chromium."""
    global _playwright, _browser  # noqa: PLW0603
    if _browser is not None and _browser.is_connected():
        return _browser
    async with _lock:
        if _browser is not None and _browser.is_connected():
            return _browser
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )
        logger.info("Playwright Chromium browser launched")
        return _browser


async def render_html_to_png(
    html: str,
    width: int = SLIDE_WIDTH,
    height: int = SLIDE_HEIGHT,
) -> bytes:
    """Render an HTML string to PNG bytes via headless Chromium."""
    browser = await _ensure_browser()
    page = await browser.new_page(
        viewport={"width": width, "height": height},
        device_scale_factor=1,
    )
    try:
        await page.set_content(html, wait_until="networkidle")
        return await page.screenshot(
            type="png",
            clip={"x": 0, "y": 0, "width": width, "height": height},
        )
    finally:
        await page.close()


async def shutdown() -> None:
    """Close browser and Playwright. Call on worker shutdown."""
    global _playwright, _browser  # noqa: PLW0603
    if _browser is not None:
        await _browser.close()
        _browser = None
    if _playwright is not None:
        await _playwright.stop()
        _playwright = None
    logger.info("Playwright browser shut down")

# spotify_checker.py
import logging
import traceback
from typing import Optional, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext

logger = logging.getLogger(__name__)

class SpotifyChecker:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.playwright = None
        self._init_complete = False

    async def initialize(self):
        if self._init_complete:
            return
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/96.0"
        )
        self._init_complete = True
        logger.info("Playwright initialized.")

    async def close(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self._init_complete = False

    async def check_account(self, email: str, password: str) -> Tuple[bool, str]:
        if not self._init_complete:
            await self.initialize()

        try:
            page = await self.context.new_page()
            await page.goto("https://accounts.spotify.com/en/login", timeout=30000)
            await page.fill('#login-username', email)
            await page.fill('#login-password', password)
            await page.click('#login-button')
            await page.wait_for_timeout(8000)

            if "login" in page.url:
                await page.close()
                return False, "Login failed"

            await page.goto("https://www.spotify.com/account/subscription", timeout=30000)
            await page.wait_for_selector("body", timeout=15000)
            text = (await page.inner_text("body")).lower()
            await page.close()

            if "votre abonnement" in text and "spotify sans abonnement" in text:
                return True, "Free"
            elif "premium" in text:
                return True, "Premium"
            elif "family" in text:
                return True, "Family"
            elif "student" in text:
                return True, "Student"
            else:
                return True, "Unknown"

        except Exception as e:
            traceback.print_exc()
            return False, f"Error: {str(e)}"

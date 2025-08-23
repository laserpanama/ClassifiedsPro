import asyncio
from playwright.async_api import async_playwright
from app.backend.models.account import Account
from app.backend.models.ad import Ad
import logging

logger = logging.getLogger(__name__)

async def post_ad_to_wanuncios(account: Account, ad: Ad) -> bool:
    """
    Automates the process of posting an ad to wanuncios.com using Playwright.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            # 1. Login
            logger.info(f"Navigating to login page for {account.email}...")
            await page.goto("https://www.wanuncios.com/gestionar/")

            await page.fill('input[name="email"]', account.email)
            await page.fill('input[name="password"]', account.wanuncios_password)

            # CAPTCHA handling is a major challenge.
            # In a real-world scenario, a third-party CAPTCHA solving service would be needed here.
            logger.warning("CAPTCHA found on login page. Attempting to proceed without solving...")

            await page.click('button:has-text("Iniciar sesión")')

            # Wait for navigation after login
            try:
                await page.wait_for_url("**/gestionar/mis-anuncios", timeout=10000)
                logger.info("Login successful.")
            except Exception:
                logger.error("Login failed. Could not navigate to 'mis-anuncios'. Check credentials or CAPTCHA.")
                await page.screenshot(path="login_failed.png")
                await browser.close()
                return False

            # 2. Navigate to ad posting page
            logger.info("Navigating to ad posting page...")
            await page.goto("https://panama.wanuncios.com/publicar/")

            # 3. Fill out the ad form
            logger.info(f"Filling out form for ad: {ad.title}")

            # These selectors are based on my research and may need adjustment
            await page.select_option('select[name="provincia"]', label=ad.province)
            await page.select_option('select[name="categoria"]', label=ad.category)
            await asyncio.sleep(1) # Simple wait for subcategories to potentially load
            await page.select_option('select[name="subcategoria"]', label=ad.subcategory)

            await page.fill('input[name="titulo"]', ad.title)
            await page.fill('textarea[name="descripcion"]', ad.description)

            if ad.price:
                await page.fill('input[name="precio"]', str(ad.price))
            if ad.zone:
                await page.fill('input[name="zona"]', ad.zone)

            await page.check('input[name="acepto_condiciones"]')

            logger.warning("CAPTCHA found on posting page. Attempting to proceed without solving...")

            # 4. Submit the form
            await page.click('button:has-text("Enviar Anuncio")')

            # 5. Verify success
            try:
                await page.wait_for_url("**/anuncio-publicado.html", timeout=15000)
                logger.info("Ad posted successfully!")
                await browser.close()
                return True
            except Exception:
                logger.error("Ad posting may have failed. Did not navigate to success URL.")
                await page.screenshot(path="ad_posting_failed.png")
                await browser.close()
                return False

        except Exception as e:
            logger.error(f"An error occurred during automation: {e}")
            await page.screenshot(path="automation_error.png")
            await browser.close()
            return False

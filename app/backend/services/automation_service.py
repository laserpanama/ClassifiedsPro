"""
Playwright-based automation for posting ads to wanuncios.com.

IMPORTANT: The CSS selectors, URLs and CAPTCHA site keys below are placeholders
taken from an initial draft and have NOT been verified against the live site.
They must be inspected and updated before this can run reliably. See the
"Automation" section of the README.
"""
import asyncio
import os
import tempfile

from playwright.async_api import async_playwright

from app.backend.models.account import Account
from app.backend.models.ad import Ad
from app.backend.services import captcha_service, ad_service
from app.backend.utils import utcnow
import logging

logger = logging.getLogger(__name__)

LOGIN_PAGE_URL = "https://www.wanuncios.com/gestionar/"
POST_PAGE_URL = "https://panama.wanuncios.com/publicar/"

# Placeholder site keys (Google's public reCAPTCHA test keys) — override via env.
LOGIN_SITE_KEY = os.getenv("WANUNCIOS_LOGIN_SITE_KEY", "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI")
POST_SITE_KEY = os.getenv("WANUNCIOS_POST_SITE_KEY", "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI")


def _screenshot_path(name: str) -> str:
    directory = os.getenv("AUTOMATION_SCREENSHOT_DIR") or tempfile.gettempdir()
    stamp = utcnow().strftime("%Y%m%d-%H%M%S")
    return os.path.join(directory, f"{name}-{stamp}.png")


# --- Helper Functions ---
async def get_captcha_token_with_script(site_key: str, page_url: str) -> str | None:
    """
    Placeholder for solving a CAPTCHA with a local solver app.
    Not implemented — always returns None so callers can fail cleanly.
    """
    logger.warning(
        "Script-based CAPTCHA solving is not implemented. "
        "Use captcha_solving_method='api' (2captcha) or 'manual'."
    )
    return None


async def get_captcha_token(page, method: str, site_key: str, page_url: str, g_recaptcha_response_id: str) -> bool:
    """Obtains a CAPTCHA token (per method) and injects it into the page."""
    token = None
    if method == "api":
        logger.info(f"Solving CAPTCHA for {page_url} using 2captcha API...")
        token = await captcha_service.solve_recaptcha_v2(site_key, page_url)
    elif method == "script":
        token = await get_captcha_token_with_script(site_key, page_url)
    elif method == "manual":
        logger.warning("Manual CAPTCHA solving selected — pausing 60s for user intervention (non-headless only).")
        await asyncio.sleep(60)
        return True
    else:
        logger.error(f"Unknown CAPTCHA solving method: {method}")
        return False

    if not token:
        logger.error(f"Could not obtain CAPTCHA token using method '{method}'.")
        return False

    logger.info("CAPTCHA token obtained. Injecting into page.")
    # Pass arguments separately — never interpolate a token into JS source.
    await page.evaluate(
        """([elementId, value]) => {
            const el = document.getElementById(elementId);
            if (el) { el.innerHTML = value; }
        }""",
        [g_recaptcha_response_id, token],
    )
    return True


# --- Main Automation Service ---
async def post_ad_to_wanuncios(account: Account, ad: Ad, db=None) -> bool:
    """
    Posts an ad to wanuncios.com. When a database handle is provided, the
    outcome is recorded (ads.last_published_at + publish_history audit rows).
    """
    is_headless = account.captcha_solving_method in ["api", "script"]
    logger.info(f"Attempting to post ad '{ad.title}' ({ad.id}) as {account.email} using '{account.captcha_solving_method}' method.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=is_headless)
        page = await browser.new_page()
        try:
            # 1. Login
            await page.goto(LOGIN_PAGE_URL)

            if not await get_captcha_token(page, account.captcha_solving_method, LOGIN_SITE_KEY, LOGIN_PAGE_URL, "g-recaptcha-response"):
                if account.captcha_solving_method == "api":
                    raise RuntimeError("Failed to solve login CAPTCHA.")

            await page.fill('input[name="email"]', account.email)
            await page.fill('input[name="password"]', account.wanuncios_password)

            if not is_headless:
                logger.info("Pausing for manual login submission...")
                await asyncio.sleep(10)

            await page.click('button:has-text("Iniciar sesión")')

            try:
                await page.wait_for_url("**/gestionar/mis-anuncios", timeout=15000)
                logger.info("Login successful.")
            except Exception:
                logger.error("Login failed. Check credentials or CAPTCHA token.")
                await page.screenshot(path=_screenshot_path("login_failed"))
                return await _finish(db, ad, account, False, "login failed")

            # 2. Post ad
            logger.info("Navigating to ad posting page...")
            await page.goto(POST_PAGE_URL)

            logger.info(f"Filling out form for ad: {ad.title}")
            await page.select_option('select[name="provincia"]', label=ad.province)
            await page.select_option('select[name="categoria"]', label=ad.category)
            await asyncio.sleep(1)
            await page.select_option('select[name="subcategoria"]', label=ad.subcategory)
            await page.fill('input[name="titulo"]', ad.title)
            await page.fill('textarea[name="descripcion"]', ad.description)
            await page.check('input[name="acepto_condiciones"]')

            if not await get_captcha_token(page, account.captcha_solving_method, POST_SITE_KEY, POST_PAGE_URL, "g-recaptcha-response-1"):
                if account.captcha_solving_method == "api":
                    raise RuntimeError("Failed to solve post CAPTCHA.")

            if not is_headless:
                logger.info("Pausing for manual ad submission...")
                await asyncio.sleep(10)

            await page.click('button:has-text("Enviar Anuncio")')

            try:
                await page.wait_for_url("**/anuncio-publicado.html", timeout=20000)
                logger.info("Ad posted successfully!")
                return await _finish(db, ad, account, True, "posted")
            except Exception:
                logger.error("Ad posting may have failed — success URL not reached.")
                await page.screenshot(path=_screenshot_path("ad_posting_failed"))
                return await _finish(db, ad, account, False, "success URL not reached")

        except Exception as e:
            logger.exception(f"An error occurred during automation: {e}")
            try:
                await page.screenshot(path=_screenshot_path("automation_error"))
            except Exception:
                pass
            return await _finish(db, ad, account, False, str(e))
        finally:
            await browser.close()


async def _finish(db, ad: Ad, account: Account, success: bool, detail: str) -> bool:
    if db is not None:
        try:
            if success:
                await ad_service.mark_published(db, ad.id)
            await ad_service.record_publish_result(db, ad.id, account.id, "success" if success else "failed", detail)
        except Exception as e:
            logger.error(f"Could not record publish outcome for ad {ad.id}: {e}")
    return success

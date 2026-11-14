"""2captcha client for reCAPTCHA v2. Fully async (httpx) — no event-loop blocking."""
import asyncio
import os
import logging

import httpx

logger = logging.getLogger(__name__)

SUBMIT_URL = "https://2captcha.com/in.php"
RESULT_URL = "https://2captcha.com/res.php"
POLL_DELAY_SECONDS = 5
MAX_POLLS = 24  # ~120 seconds


async def solve_recaptcha_v2(site_key: str, page_url: str) -> str | None:
    """
    Solves a reCAPTCHA v2 using 2captcha.com.

    :param site_key: The reCAPTCHA site key from the target page.
    :param page_url: The URL of the page with the reCAPTCHA.
    :return: The g-recaptcha-response token, or None on failure.
    """
    api_key = os.getenv("TWOCAPTCHA_API_KEY")
    if not api_key:
        logger.error("TWOCAPTCHA_API_KEY not found in environment variables.")
        return None

    async with httpx.AsyncClient(timeout=30) as client:
        # 1. Submit the CAPTCHA for solving
        try:
            response = await client.post(
                SUBMIT_URL,
                params={
                    "key": api_key,
                    "method": "userrecaptcha",
                    "googlekey": site_key,
                    "pageurl": page_url,
                    "json": 1,
                },
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as e:
            logger.error(f"Error submitting CAPTCHA to 2captcha: {e}")
            return None

        if data.get("status") != 1:
            logger.error(f"2Captcha submission failed: {data.get('request')}")
            return None
        request_id = data.get("request")
        logger.info(f"CAPTCHA submitted successfully. Request ID: {request_id}")

        # 2. Poll for the result
        for _ in range(MAX_POLLS):
            await asyncio.sleep(POLL_DELAY_SECONDS)
            try:
                response = await client.get(
                    RESULT_URL,
                    params={"key": api_key, "action": "get", "id": request_id, "json": 1},
                )
                response.raise_for_status()
                data = response.json()
            except (httpx.HTTPError, ValueError) as e:
                logger.error(f"Error polling for CAPTCHA result: {e}")
                return None

            if data.get("status") == 1:
                logger.info("CAPTCHA solved successfully.")
                return data.get("request")
            if data.get("request") == "CAPCHA_NOT_READY":
                logger.info("CAPTCHA not ready, polling again...")
                continue
            logger.error(f"Failed to solve CAPTCHA: {data.get('request')}")
            return None

    logger.error("CAPTCHA solving timed out.")
    return None

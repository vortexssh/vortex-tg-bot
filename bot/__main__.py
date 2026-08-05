"""Long-polling Telegram bot for Vortex account linking."""

from __future__ import annotations

import asyncio
import logging
import re

import httpx

from bot.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("vortex_tg_bot")

START_RE = re.compile(r"^/start(?:@\w+)?(?:\s+(\S+))?$", re.IGNORECASE)


async def confirm_with_core(code: str, chat_id: int | str) -> tuple[bool, str]:
    settings = get_settings()
    url = f"{settings.core_url.rstrip('/')}/internal/telegram/confirm"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                json={"code": code, "chat_id": str(chat_id)},
                headers={"X-Bot-Api-Key": settings.bot_api_key},
            )
        if response.status_code == 204:
            return True, "Linked! You will receive Vortex billing reminders here."
        try:
            data = response.json()
            msg = data.get("error", {}).get("message") or response.text
        except Exception:
            msg = response.text
        return False, f"Link failed: {msg}"
    except Exception as exc:
        logger.exception("Core confirm failed")
        return False, f"Could not reach Vortex Core: {exc}"


async def send_message(token: str, chat_id: int | str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    async with httpx.AsyncClient(timeout=15.0) as client:
        await client.post(url, json={"chat_id": chat_id, "text": text})


async def handle_update(token: str, update: dict) -> None:
    message = update.get("message") or update.get("edited_message")
    if not message:
        return
    text = (message.get("text") or "").strip()
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if chat_id is None:
        return

    match = START_RE.match(text)
    if not match:
        await send_message(
            token,
            chat_id,
            "VortexSSH bot.\nOpen Settings → Notifications in the web console to link your account.",
        )
        return

    code = match.group(1)
    if not code:
        await send_message(
            token,
            chat_id,
            "Missing link code. Use the deep link from Vortex Web Settings.",
        )
        return

    ok, reply = await confirm_with_core(code, chat_id)
    await send_message(token, chat_id, reply)
    if ok:
        logger.info("Linked chat_id=%s", chat_id)


async def poll_loop() -> None:
    settings = get_settings()
    token = settings.bot_token
    offset = 0
    logger.info("Vortex Telegram bot started (core=%s)", settings.core_url)
    async with httpx.AsyncClient(timeout=60.0) as client:
        while True:
            try:
                response = await client.get(
                    f"https://api.telegram.org/bot{token}/getUpdates",
                    params={"timeout": 50, "offset": offset},
                )
                response.raise_for_status()
                data = response.json()
                for update in data.get("result") or []:
                    offset = max(offset, int(update["update_id"]) + 1)
                    try:
                        await handle_update(token, update)
                    except Exception:
                        logger.exception("Failed handling update")
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Polling error")
                await asyncio.sleep(3)


def main() -> None:
    asyncio.run(poll_loop())


if __name__ == "__main__":
    main()

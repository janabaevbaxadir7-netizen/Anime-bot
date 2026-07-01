import logging
import time
import traceback
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message

import config

logger = logging.getLogger("yuki_bot")


class ThrottlingMiddleware(BaseMiddleware):
    """Oddiy anti-flood: bir foydalanuvchi THROTTLE_RATE_LIMIT soniyadan tezroq
    xabar yuborsa, xabar e'tiborsiz qoldiriladi (DB va Telegram API ga ortiqcha
    yuk tushmasligi uchun)."""

    def __init__(self, rate_limit: float = None):
        self.rate_limit = rate_limit or config.THROTTLE_RATE_LIMIT
        self._last_call: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is not None:
            now = time.monotonic()
            last = self._last_call.get(user.id, 0)
            if now - last < self.rate_limit:
                return  # xabarni jimgina o'tkazib yuboramiz
            self._last_call[user.id] = now
        return await handler(event, data)


class ErrorLoggingMiddleware(BaseMiddleware):
    """Har qanday handler xatoligini ushlaydi: faylga yozadi va
    super-adminlarga Telegram orqali xabar beradi, bot butunlay yiqilib
    qolmasligi va muammo tezda ko'rinishi uchun."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            logger.exception("Handlerda xatolik yuz berdi")
            bot = data.get("bot")
            if bot is not None:
                short_trace = traceback.format_exc()[-1500:]
                for admin_id in config.SUPER_ADMIN_IDS:
                    try:
                        await bot.send_message(
                            admin_id,
                            f"⚠️ <b>Botda xatolik!</b>\n\n<code>{short_trace}</code>",
                        )
                    except Exception:
                        pass
            # Foydalanuvchini "osilib qolgan" holatda qoldirmaslik uchun xabar beramiz
            if isinstance(event, Message):
                try:
                    await event.answer("😔 Kutilmagan xatolik yuz berdi. Admin xabardor qilindi.")
                except Exception:
                    pass
                  

import asyncio
import logging
from logging.handlers import RotatingFileHandler

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import config
from db import init_db
import handlers_admin
import handlers_user
from middlewares import ThrottlingMiddleware, ErrorLoggingMiddleware


def setup_logging():
    handler = RotatingFileHandler(config.LOG_FILE, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    root.addHandler(logging.StreamHandler())  # konsolga ham chiqarib turadi


async def main():
    config.validate()
    setup_logging()
    logger = logging.getLogger("yuki_bot")

    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware'lar — barcha xabar va callbacklarga qo'llanadi
    dp.message.middleware(ErrorLoggingMiddleware())
    dp.callback_query.middleware(ErrorLoggingMiddleware())
    dp.message.middleware(ThrottlingMiddleware())

    await init_db()
    dp.include_router(handlers_admin.router)
    dp.include_router(handlers_user.router)

    logger.info("⛩️✨ %s uyg'ondi! Bot ishga tushdi...", config.BOT_NAME)
    print(f"⛩️✨ {config.BOT_NAME} uyg'ondi! Bot ishga tushdi...")

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
    

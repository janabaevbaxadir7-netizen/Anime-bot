import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import config
from db import init_db

import admin
import dev
import help
import premium
import earn
import anime
import start
import inline


async def main():
    config.validate()
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # MUHIM: tartib shu bo'yicha bo'lishi kerak!
    # admin.py dagi matn-tugmalar (masalan "⛩ Kanallar") va aniq buyruqlar
    # start.py dagi "har qanday matn" catch-all handleridan OLDIN turishi shart.
    dp.include_router(admin.router)
    dp.include_router(dev.router)
    dp.include_router(help.router)
    dp.include_router(premium.router)
    dp.include_router(earn.router)
    dp.include_router(anime.router)
    dp.include_router(inline.router)  # "Ulashish" tugmasi uchun inline mode
    dp.include_router(start.router)  # eng oxirida, chunki bu yerda "F.text" catch-all bor

    await init_db()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

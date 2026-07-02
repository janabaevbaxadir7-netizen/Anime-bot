import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database.db import init_db

from handlers import start, anime, premium, help, dev, admin


async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # MUHIM: tartib shu bo'yicha bo'lishi kerak!
    # Aniq buyruqlar (/admin, premium_on/off) start.py dagi "har qanday matn"
    # handleridan OLDIN turishi shart, aks holda ular ushlanib qolmaydi.
    dp.include_router(admin.router)
    dp.include_router(dev.router)
    dp.include_router(help.router)
    dp.include_router(premium.router)
    dp.include_router(anime.router)
    dp.include_router(start.router)  # eng oxirida, chunki bu yerda "F.text" catch-all bor

    await init_db()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config


async def main_menu_kb() -> InlineKeyboardMarkup:
    # MUHIM: bu tugma har doim ASOSIY reklama kanaliga (config.MAIN_CHANNEL_URL)
    # ochiladi — majburiy obuna kanallariga BOG'LIQ EMAS. Ilgari birinchi majburiy
    # obuna kanalining havolasidan foydalanilardi, bu esa kanal ro'yxati
    # o'zgarganda yoki bo'sh bo'lganda tugmani buzib qo'yardi.
    rows = [[InlineKeyboardButton(text="📺 Ko'proq Animelar", url=config.MAIN_CHANNEL_URL)]]
    rows.append([InlineKeyboardButton(text="⬇️ Saqlangan Animelar", callback_data="saved_animes")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Bosh Menyu", callback_data="main_menu")],
        ]
    )

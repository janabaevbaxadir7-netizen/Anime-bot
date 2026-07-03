from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
import crud


async def main_menu_kb() -> InlineKeyboardMarkup:
    rows = []
    # Agar admin kanal qo'shgan bo'lsa (Kanallar bo'limida), o'sha kanalga yo'naltiradi.
    # Aks holda, tugma ko'rsatilmaydi (noto'g'ri joyga olib bormasligi uchun).
    channels = await crud.get_all_channels()
    if channels and channels[0].url:
        rows.append([InlineKeyboardButton(text="📺 Ko'proq Animelar", url=channels[0].url)])
    rows.append([InlineKeyboardButton(text="⬇️ Saqlangan Animelar", callback_data="saved_animes")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Bosh Menyu", callback_data="main_menu")],
        ]
    )

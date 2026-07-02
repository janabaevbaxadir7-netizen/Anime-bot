from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import SUPPORT_CHAT


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📺 Ko'proq Animelar", url=SUPPORT_CHAT)],
            [InlineKeyboardButton(text="⬇️ Saqlangan Animelar", callback_data="saved_animes")],
        ]
    )


def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Bosh Menyu", callback_data="main_menu")],
        ]
    )

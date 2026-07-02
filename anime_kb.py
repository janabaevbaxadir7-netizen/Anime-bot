from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import Anime


def anime_list_kb(animes: list[Anime]) -> InlineKeyboardMarkup:
    """Anime nomlaridan iborat tugmalar ro'yxati (/rand, /top, /last uchun)."""
    rows = [
        [InlineKeyboardButton(text=anime.title, callback_data=f"anime_{anime.code}")]
        for anime in animes
    ]
    rows.append([InlineKeyboardButton(text="🏠 Bosh Menyu", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def episode_kb(anime_code: int, episode_count: int) -> InlineKeyboardMarkup:
    """1,2,3...N qism tugmalari + barchasini yuklab olish."""
    buttons = []
    row = []
    for i in range(1, episode_count + 1):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"ep_{anime_code}_{i}"))
        if len(row) == 7:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(text="⚡ Barcha qismni yuklab olish", callback_data=f"all_{anime_code}")
    ])
    buttons.append([
        InlineKeyboardButton(text="↪️ Ulashish", switch_inline_query=str(anime_code)),
        InlineKeyboardButton(text="⬇️ Saqlash", callback_data=f"save_{anime_code}"),
    ])
    buttons.append([InlineKeyboardButton(text="🏠 Bosh Menyu", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

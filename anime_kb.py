from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from models import Anime


def anime_list_kb(animes: list[Anime]) -> InlineKeyboardMarkup:
    """Anime nomlaridan iborat tugmalar ro'yxati (/rand, /top, /last uchun)."""
    rows = [
        [InlineKeyboardButton(text=anime.title, callback_data=f"anime_{anime.code}")]
        for anime in animes
    ]
    rows.append([InlineKeyboardButton(text="🏠 Bosh Menyu", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


EPISODES_PER_PAGE = 20


def episode_kb(anime_code: int, episode_count: int, has_trailer: bool = False, page: int = 0) -> InlineKeyboardMarkup:
    """1,2,3...N qism tugmalari (20 tadan sahifalab) + barchasini yuklab olish."""
    buttons = []
    start = page * EPISODES_PER_PAGE
    end = min(start + EPISODES_PER_PAGE, episode_count)

    row = []
    for i in range(start + 1, end + 1):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"ep_{anime_code}_{i}"))
        if len(row) == 7:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    total_pages = max(1, (episode_count - 1) // EPISODES_PER_PAGE + 1) if episode_count else 1
    if total_pages > 1:
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"eppg_{anime_code}_{page-1}"))
        nav.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton(text="➡️", callback_data=f"eppg_{anime_code}_{page+1}"))
        buttons.append(nav)

    if has_trailer:
        buttons.append([InlineKeyboardButton(text="🎥 Trailer", callback_data=f"trailer_{anime_code}")])

    buttons.append([
        InlineKeyboardButton(text="⚡ Barcha qismni yuklab olish", callback_data=f"all_{anime_code}")
    ])
    buttons.append([
        InlineKeyboardButton(text="↪️ Ulashish", switch_inline_query=str(anime_code)),
        InlineKeyboardButton(text="⬇️ Saqlash", callback_data=f"save_{anime_code}"),
    ])
    buttons.append([InlineKeyboardButton(text="🏠 Bosh Menyu", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

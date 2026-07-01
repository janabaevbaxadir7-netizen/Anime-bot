from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
import texts


def gender_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.GENDER_SENPAI_BTN, callback_data="gender:senpai")
    kb.button(text=texts.GENDER_HIME_BTN, callback_data="gender:hime")
    kb.adjust(1)
    return kb.as_markup()


def subscribe_kb(channels):
    kb = InlineKeyboardBuilder()
    for ch in channels:
        kb.button(text=f"📢 {ch.title or ch.chat_id}", url=ch.url)
    kb.button(text=texts.SUBSCRIBE_CHECK_BTN, callback_data="check_sub")
    kb.adjust(1)
    return kb.as_markup()


def main_menu_kb():
    kb = [
        [KeyboardButton(text=texts.MENU_SEARCH), KeyboardButton(text=texts.MENU_TOP)],
        [KeyboardButton(text=texts.MENU_HISTORY), KeyboardButton(text=texts.MENU_PREMIUM)],
        [KeyboardButton(text=texts.MENU_FEEDBACK), KeyboardButton(text=texts.MENU_ADS)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def cancel_kb():
    kb = [[KeyboardButton(text=texts.CANCEL_BTN)]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def episodes_grid_kb(anime, page=0):
    kb = InlineKeyboardBuilder()
    eps = anime.episodes
    per_page = 14
    start = page * per_page
    end = min(start + per_page, len(eps))
    page_eps = eps[start:end]
    total_pages = (len(eps) - 1) // per_page + 1

    for ep in page_eps:
        kb.button(text=str(ep.episode_num), callback_data=f"ep:{anime.id}:{ep.episode_num}")
    kb.adjust(7)

    nav = []
    if page > 0:
        nav.append(("⬅️", f"eppage:{anime.id}:{page-1}"))
    if total_pages > 1:
        nav.append((f"• {page+1}/{total_pages} •", "noop"))
    if page < total_pages - 1:
        nav.append(("➡️", f"eppage:{anime.id}:{page+1}"))

    if nav:
        row_kb = InlineKeyboardBuilder()
        for text, cb in nav:
            row_kb.button(text=text, callback_data=cb)
        kb.attach(row_kb)

    kb.button(text=texts.LIKE_BTN, callback_data=f"rate:{anime.id}:like")
    kb.button(text=texts.DISLIKE_BTN, callback_data=f"rate:{anime.id}:dislike")
    kb.button(text=texts.SHARE_BTN, switch_inline_query=f"{anime.code}")
    kb.adjust(7, *([3] if nav else []), 2, 1)
    return kb.as_markup()


def episode_player_kb(anime, current_ep, total):
    kb = InlineKeyboardBuilder()
    if current_ep > 1:
        kb.button(text=texts.PREV_BTN, callback_data=f"ep:{anime.id}:{current_ep-1}")
    kb.button(text=f"• {current_ep}/{total} •", callback_data="noop")
    if current_ep < total:
        kb.button(text=texts.NEXT_BTN, callback_data=f"ep:{anime.id}:{current_ep+1}")
    kb.button(text=texts.ALL_EPISODES_BTN, callback_data=f"allep:{anime.id}:0")
    kb.button(text=texts.LIKE_BTN, callback_data=f"rate:{anime.id}:like")
    kb.button(text=texts.DISLIKE_BTN, callback_data=f"rate:{anime.id}:dislike")
    kb.button(text=texts.SHARE_BTN, switch_inline_query=f"{anime.code}")
    kb.adjust(3, 1, 2, 1)
    return kb.as_markup()


def premium_kb(admin_username=None):
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.PREMIUM_BTN_1, callback_data="premium:1")
    kb.button(text=texts.PREMIUM_BTN_3, callback_data="premium:3")
    kb.button(text=texts.PREMIUM_BTN_6, callback_data="premium:6")
    if admin_username:
        kb.button(text="💬 Admin bilan bog'lanish", url=f"https://t.me/{admin_username}")
    kb.adjust(1)
    return kb.as_markup()


def ads_contact_kb(admin_username=None):
    kb = InlineKeyboardBuilder()
    if admin_username:
        kb.button(text="💬 Admin bilan bog'lanish", url=f"https://t.me/{admin_username}")
    return kb.as_markup()
    

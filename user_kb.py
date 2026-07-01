from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import texts
import db


def gender_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.GENDER_SENPAI_BTN, callback_data="gender:senpai")
    kb.button(text=texts.GENDER_HIME_BTN, callback_data="gender:hime")
    kb.adjust(2)
    return kb.as_markup()


def subscribe_kb(channels) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for ch in channels:
        kb.button(text=f"⛩️ {ch.title or ch.chat_id}", url=ch.url)
    kb.button(text=texts.SUBSCRIBE_CHECK_BTN, callback_data="check_sub")
    kb.adjust(1)
    return kb.as_markup()


def main_menu_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text=texts.MENU_SEARCH), KeyboardButton(text=texts.MENU_TOP)],
        [KeyboardButton(text=texts.MENU_HISTORY), KeyboardButton(text=texts.MENU_FEEDBACK)],
        [KeyboardButton(text=texts.MENU_ADS)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def episodes_grid_kb(anime) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for ep in anime.episodes:
        kb.button(text=str(ep.episode_num), callback_data=f"ep:{anime.id}:{ep.episode_num}")
    kb.adjust(6)
    return kb.as_markup()


def episode_player_kb(anime, current_ep: int, total: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if current_ep > 1:
        kb.button(text=texts.PREV_BTN, callback_data=f"ep:{anime.id}:{current_ep - 1}")
    if current_ep < total:
        kb.button(text=texts.NEXT_BTN, callback_data=f"ep:{anime.id}:{current_ep + 1}")
    kb.button(text=texts.ALL_EPISODES_BTN, callback_data=f"allep:{anime.id}")
    kb.button(text=texts.LIKE_BTN, callback_data=f"rate:{anime.id}:like")
    kb.button(text=texts.DISLIKE_BTN, callback_data=f"rate:{anime.id}:dislike")
    kb.button(text=texts.SHARE_BTN, switch_inline_query=anime.code)
    kb.adjust(2, 1, 2, 1)
    return kb.as_markup()


def ads_contact_kb(admin_username: str | None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if admin_username:
        kb.button(text="💌 Admin bilan bog'lanish", url=f"https://t.me/{admin_username}")
    return kb.as_markup()

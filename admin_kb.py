from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import texts


def admin_menu_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text=texts.ADMIN_MENU_ADD), KeyboardButton(text=texts.ADMIN_MENU_ADD_EP)],
        [KeyboardButton(text=texts.ADMIN_MENU_LIST), KeyboardButton(text=texts.ADMIN_MENU_CHANNELS)],
        [KeyboardButton(text=texts.ADMIN_MENU_BROADCAST), KeyboardButton(text=texts.ADMIN_MENU_FEEDBACK)],
        [KeyboardButton(text=texts.ADMIN_MENU_STATS), KeyboardButton(text=texts.BACK_BTN)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def finish_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.FINISH_BTN, callback_data="finish_adding")
    return kb.as_markup()


def anime_list_kb(anime_list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for a in anime_list:
        kb.button(text=f"🎴 {a.title} ({a.code})", callback_data=f"admin_view:{a.id}")
    kb.adjust(1)
    return kb.as_markup()


def anime_manage_kb(anime) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🗑 O'chirish", callback_data=f"admin_del:{anime.id}")
    kb.button(text=texts.BACK_BTN, callback_data="admin_list_back")
    kb.adjust(1)
    return kb.as_markup()


def channels_manage_kb(channels, sub_on: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    status = "🟢 Yoqilgan" if sub_on else "🔴 O'chirilgan"
    kb.button(text=f"Majburiy obuna: {status}", callback_data="toggle_sub")
    for ch in channels:
        kb.button(text=f"🗑 {ch.title or ch.chat_id}", callback_data=f"del_channel:{ch.id}")
    kb.button(text="➕ Yangi kanal qo'shish", callback_data="add_channel")
    kb.adjust(1)
    return kb.as_markup()

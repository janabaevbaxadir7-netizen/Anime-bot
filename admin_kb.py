from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import texts


def admin_menu_kb():
    kb = [
        [KeyboardButton(text=texts.ADMIN_MENU_ADD), KeyboardButton(text=texts.ADMIN_MENU_ADD_EP)],
        [KeyboardButton(text=texts.ADMIN_MENU_LIST), KeyboardButton(text=texts.ADMIN_MENU_CHANNELS)],
        [KeyboardButton(text=texts.ADMIN_MENU_BROADCAST), KeyboardButton(text=texts.ADMIN_MENU_FEEDBACK)],
        [KeyboardButton(text=texts.ADMIN_MENU_STATS), KeyboardButton(text=texts.ADMIN_MENU_PREMIUM)],
        [KeyboardButton(text=texts.BACK_BTN)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def finish_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.FINISH_BTN, callback_data="finish_adding")
    kb.adjust(1)
    return kb.as_markup()


def anime_list_kb(anime_list, page=0):
    kb = InlineKeyboardBuilder()
    per_page = 8
    start = page * per_page
    end = min(start + per_page, len(anime_list))
    total_pages = max(1, (len(anime_list) - 1) // per_page + 1)

    for a in anime_list[start:end]:
        ep_count = len(a.episodes) if hasattr(a, 'episodes') and a.episodes else 0
        kb.button(
            text=f"🎬 {a.title} ({ep_count} qism) | #{a.code}",
            callback_data=f"admin_view:{a.id}"
        )

    nav = InlineKeyboardBuilder()
    if page > 0:
        nav.button(text="⬅️", callback_data=f"alist:{page-1}")
    if total_pages > 1:
        nav.button(text=f"{page+1}/{total_pages}", callback_data="noop")
    if page < total_pages - 1:
        nav.button(text="➡️", callback_data=f"alist:{page+1}")

    if total_pages > 1:
        kb.attach(nav)

    kb.adjust(1)
    return kb.as_markup()


def anime_manage_kb(anime):
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Qism qo'shish", callback_data=f"aquick_ep:{anime.id}")
    kb.button(text="✏️ Nomni o'zgartirish", callback_data=f"arename:{anime.id}")
    kb.button(text="🗑 O'chirish", callback_data=f"admin_del:{anime.id}")
    kb.button(text=texts.BACK_BTN, callback_data="admin_list_back:0")
    kb.adjust(1)
    return kb.as_markup()


def channels_manage_kb(channels, sub_on):
    kb = InlineKeyboardBuilder()
    status = "🟢 Yoqilgan" if sub_on else "🔴 O'chirilgan"
    kb.button(text=f"Majburiy obuna: {status}", callback_data="toggle_sub")
    for ch in channels:
        kb.button(text=f"🗑 {ch.title or ch.chat_id}", callback_data=f"del_channel:{ch.id}")
    kb.button(text="➕ Kanal qo'shish", callback_data="add_channel")
    kb.adjust(1)
    return kb.as_markup()


def confirm_delete_kb(anime_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Ha, o'chir", callback_data=f"confirm_del:{anime_id}")
    kb.button(text="❌ Bekor", callback_data=f"admin_view:{anime_id}")
    kb.adjust(2)
    return kb.as_markup()
    

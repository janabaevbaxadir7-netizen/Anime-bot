from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ── ASOSIY ADMIN PANEL (pastki doimiy menyu) ──
def admin_panel_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="⛩ Kanallar"), KeyboardButton(text="🎬 Animelar")],
        [KeyboardButton(text="📢 Xabarnoma"), KeyboardButton(text="👤 Foydalanuvchi")],
        [KeyboardButton(text="🛡 Adminlar"), KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="📁 Ma'lumotlar"), KeyboardButton(text="📝 Post tayyorlash")],
        [KeyboardButton(text="📨 Xabarlar")],
        [KeyboardButton(text="🔄 /start")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Bekor qilish")]], resize_keyboard=True)


def skip_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="➡️ Skip")], [KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )


# ── ANIMELAR ──
def anime_menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Yangi Anime joylash", callback_data="am_new")
    kb.button(text="🎬 Qism joylash", callback_data="am_add_ep")
    kb.button(text="✏️ Tahrirlash", callback_data="am_edit")
    kb.button(text="🗑 O'chirish", callback_data="am_delete")
    kb.button(text="📋 To'liq ro'yxat", callback_data="am_list:0")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


def anime_list_admin_kb(anime_list, page=0, per_page=10):
    kb = InlineKeyboardBuilder()
    start, end = page * per_page, page * per_page + per_page
    for a in anime_list[start:end]:
        kb.button(text=f"{a.title} — #{a.code}", callback_data=f"am_view:{a.id}")
    total_pages = max(1, (len(anime_list) - 1) // per_page + 1)
    nav = []
    if page > 0:
        nav.append(("⬅️", f"am_list:{page-1}"))
    if total_pages > 1:
        nav.append((f"{page+1}/{total_pages}", "noop"))
    if page < total_pages - 1:
        nav.append(("➡️", f"am_list:{page+1}"))
    kb.adjust(1)
    if nav:
        row_kb = InlineKeyboardBuilder()
        for text, cb in nav:
            row_kb.button(text=text, callback_data=cb)
        kb.attach(row_kb)
    return kb.as_markup()


def anime_edit_actions_kb(anime_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Nomi", callback_data=f"aedit_title:{anime_id}")
    kb.button(text="📝 Tavsifi", callback_data=f"aedit_desc:{anime_id}")
    kb.button(text="💎 Premium sozlash", callback_data=f"aedit_premium:{anime_id}")
    kb.button(text="🗑 Qism o'chirish", callback_data=f"aedit_delep:{anime_id}")
    kb.adjust(1)
    return kb.as_markup()


def premium_settings_kb(anime_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="🔒 Premium qilish (muddat bilan)", callback_data=f"aedit_premium_on:{anime_id}")
    kb.button(text="🔓 Premiumni olib tashlash", callback_data=f"aedit_premium_off:{anime_id}")
    kb.adjust(1)
    return kb.as_markup()


def confirm_delete_anime_kb(anime_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Ha, o'chir", callback_data=f"adel_confirm:{anime_id}")
    kb.button(text="❌ Bekor", callback_data="noop")
    kb.adjust(2)
    return kb.as_markup()


# ── KANALLAR ──
def channels_kb(channels):
    kb = InlineKeyboardBuilder()
    for i, ch in enumerate(channels, 1):
        kb.button(text=f"🗑 {i}. {ch.title or ch.chat_id}", callback_data=f"ch_del:{ch.id}")
    kb.button(text="➕ Kanal qo'shish", callback_data="ch_add")
    kb.adjust(1)
    return kb.as_markup()


# ── POST — KANAL TANLASH (ko'p tanlovli, saqlangan ro'yxatdan) ──
def post_channels_pick_kb(channels, selected_ids: set):
    kb = InlineKeyboardBuilder()
    for ch in channels:
        mark = "☑️" if ch.id in selected_ids else "⬜️"
        kb.button(text=f"{mark} {ch.title or ch.chat_id}", callback_data=f"postch_pick:{ch.id}")
        kb.button(text="🗑", callback_data=f"postch_del:{ch.id}")
    kb.button(text="➕ Yangi kanal qo'shish", callback_data="postch_new")
    if selected_ids:
        kb.button(text=f"✅ Joylash ({len(selected_ids)} ta kanalga)", callback_data="postch_confirm")
    kb.button(text="❌ Bekor qilish", callback_data="postch_cancel")
    # har bir kanal uchun 2 ta tugma (tanlash + o'chirish) bir qatorda, qolganlari alohida qatorda
    rows = [2] * len(channels) + [1] * (2 if selected_ids else 1) + [1]
    kb.adjust(*rows)
    return kb.as_markup()


# ── XABARLAR (foydalanuvchi murojaatlari) ──
def feedback_nav_kb(page: int, total: int, per_page: int = 5):
    kb = InlineKeyboardBuilder()
    total_pages = max(1, (total - 1) // per_page + 1)
    if page > 0:
        kb.button(text="⬅️", callback_data=f"fb_page:{page-1}")
    kb.button(text=f"{page+1}/{total_pages}", callback_data="noop")
    if (page + 1) * per_page < total:
        kb.button(text="➡️", callback_data=f"fb_page:{page+1}")
    kb.adjust(3)
    return kb.as_markup()


# ── ADMINLAR ──
ALL_PERMISSIONS = [
    ("anime", "🎬 Animelar"),
    ("channels", "⛩ Kanallar"),
    ("broadcast", "📢 Xabarnoma"),
    ("premium", "💎 Premium"),
    ("posts", "📝 Postlar"),
]


def admins_list_kb(super_ids, db_admins):
    kb = InlineKeyboardBuilder()
    for uid in super_ids:
        kb.button(text=f"👑 {uid} (bosh admin)", callback_data="noop")
    for a in db_admins:
        kb.button(text=f"⚙️ {a.id} — {a.full_name or 'nomsiz'}", callback_data=f"adm_view:{a.id}")
    kb.button(text="➕ Admin qo'shish", callback_data="adm_add")
    kb.adjust(1)
    return kb.as_markup()


def admin_permissions_kb(admin_id, current_perms: str):
    current = set(p.strip() for p in current_perms.split(",") if p.strip())
    kb = InlineKeyboardBuilder()
    for key, label in ALL_PERMISSIONS:
        mark = "✅" if key in current else "⬜️"
        kb.button(text=f"{mark} {label}", callback_data=f"adm_toggle:{admin_id}:{key}")
    kb.button(text="🗑 Adminlikdan olib tashlash", callback_data=f"adm_remove:{admin_id}")
    kb.button(text="⬅️ Orqaga", callback_data="adm_back_list")
    kb.adjust(1)
    return kb.as_markup()

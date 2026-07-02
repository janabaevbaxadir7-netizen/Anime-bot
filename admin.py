import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import ADMIN_IDS
from crud import get_stats, set_premium, remove_premium

router = Router()


def admin_filter(message_or_call) -> bool:
    return message_or_call.from_user.id in ADMIN_IDS


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎬 Yangi anime", callback_data="adm_new_anime"),
                InlineKeyboardButton(text="➕ Qism qo'shish", callback_data="adm_add_episode"),
            ],
            [
                InlineKeyboardButton(text="📋 Anime ro'yxati", callback_data="adm_anime_list"),
                InlineKeyboardButton(text="⛩ Kanallar", callback_data="adm_channels"),
            ],
            [
                InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="adm_broadcast"),
                InlineKeyboardButton(text="✉️ Murojaatlar", callback_data="adm_feedback"),
            ],
            [
                InlineKeyboardButton(text="📊 Statistika", callback_data="adm_stats"),
                InlineKeyboardButton(text="💎 Premium so'rovlar", callback_data="adm_premium_requests"),
            ],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm_back")],
        ]
    )


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not admin_filter(message):
        return
    await message.answer(
        "⛩ <b>Admin paneli</b> — Okaerinasai, Yaratuvchi-sama!",
        reply_markup=admin_menu_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "adm_stats")
async def admin_stats(call: CallbackQuery):
    if not admin_filter(call):
        await call.answer("⛔️ Ruxsat yo'q", show_alert=True)
        return
    s = await get_stats()
    text = (
        "⛩ <b>Admin paneli</b> — Okaerinasai, Yaratuvchi-sama!\n\n"
        "📊 <b>Bugungi holat:</b>\n"
        f"👥 Jami: {s['total_users']} ta | Bugun: +{s['today_users']}\n"
        f"💎 Premium: {s['premium_count']} ta\n"
        f"🎬 Animelar: {s['anime_count']} ta | Qismlar: {s['episode_count']} ta"
    )
    await call.message.edit_text(text, reply_markup=admin_menu_kb(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "adm_back")
async def admin_back(call: CallbackQuery):
    await call.message.delete()
    await call.answer()


# ==================== PREMIUM QO'LSHI BILAN BOSHQARISH ====================
# Format: premium_on <ID> <YYYY-MM-DD>   /   premium_off <ID>

@router.message(F.text.regexp(r"^premium_on\s+(\d+)\s+(\d{4}-\d{2}-\d{2})$"))
async def premium_on_cmd(message: Message):
    if not admin_filter(message):
        return
    import re
    match = re.match(r"^premium_on\s+(\d+)\s+(\d{4}-\d{2}-\d{2})$", message.text)
    tg_id, date_str = match.groups()
    until = datetime.datetime.strptime(date_str, "%Y-%m-%d")

    ok = await set_premium(int(tg_id), until)
    if ok:
        await message.answer(f"✅ {tg_id} foydalanuvchiga {date_str} sanagacha Premium berildi.")
    else:
        await message.answer("❌ Bunday foydalanuvchi bazada topilmadi.")


@router.message(F.text.regexp(r"^premium_off\s+(\d+)$"))
async def premium_off_cmd(message: Message):
    if not admin_filter(message):
        return
    import re
    match = re.match(r"^premium_off\s+(\d+)$", message.text)
    tg_id = match.group(1)

    ok = await remove_premium(int(tg_id))
    if ok:
        await message.answer(f"✅ {tg_id} foydalanuvchidan Premium olib tashlandi.")
    else:
        await message.answer("❌ Bunday foydalanuvchi bazada topilmadi.")

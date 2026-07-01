import asyncio
import logging

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import texts, config, db
from states import AdminStates
import admin_kb, user_kb
from filters import IsAdmin, IsSuperAdmin, is_admin_async

router = Router()
logger = logging.getLogger("yuki_bot")


async def show_admin_panel(message, state):
    await state.clear()
    users = await db.count_users()
    today = await db.count_users_today()
    premium = await db.count_premium_users()
    anime_c, ep_c = await db.count_anime_and_episodes()
    await message.answer(
        texts.ADMIN_WELCOME.format(users=users, today=today, premium=premium, anime=anime_c, episodes=ep_c),
        reply_markup=admin_kb.admin_menu_kb()
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not await is_admin_async(message.from_user.id):
        await message.answer(texts.NOT_ADMIN); return
    await show_admin_panel(message, state)


@router.message(F.text == texts.BACK_BTN, IsAdmin())
async def admin_back(message: Message, state: FSMContext):
    await show_admin_panel(message, state)


# ── ADMIN → FOYDALANUVCHI REJIMIGA O'TISH ──
@router.message(F.text == texts.ADMIN_MENU_USER_MODE, IsAdmin())
async def admin_switch_to_user_mode(message: Message, state: FSMContext):
    await state.clear()
    from handlers_user import show_main_menu
    user = await db.get_user(message.from_user.id)
    await message.answer(
        "👤 Foydalanuvchi rejimiga o'tdingiz.\n"
        "Admin panelga qaytish uchun /admin yozing."
    )
    await show_main_menu(message, user.gender if user else "")


# ── YANGI ANIME ──
@router.message(F.text == texts.ADMIN_MENU_ADD, IsAdmin())
async def admin_add_anime(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(texts.ASK_NEW_TITLE, reply_markup=user_kb.cancel_kb())
    await state.set_state(AdminStates.waiting_new_title)


@router.message(AdminStates.waiting_new_title)
async def admin_new_title(message: Message, state: FSMContext):
    if not await is_admin_async(message.from_user.id): return
    if message.text == texts.CANCEL_BTN:
        await show_admin_panel(message, state); return
    title = message.text.strip()
    code = await db.get_next_code()
    anime = await db.create_anime(code=code, title=title)
    await state.update_data(anime_id=anime.id)
    await message.answer(
        texts.NEW_ANIME_CREATED.format(title=title, code=code),
        reply_markup=admin_kb.finish_kb()
    )
    await state.set_state(AdminStates.waiting_episodes)


@router.message(AdminStates.waiting_episodes, F.video)
async def admin_ep_new(message: Message, state: FSMContext):
    data = await state.get_data()
    anime_id = data.get("anime_id")
    if not anime_id: return
    num = await db.add_episode(anime_id, message.video.file_id, message.caption or "")
    await message.answer(texts.EPISODE_ADDED.format(num=num), reply_markup=admin_kb.finish_kb())


@router.callback_query(F.data == "finish_adding")
async def finish_adding(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    anime_id = data.get("anime_id")
    if anime_id:
        anime = await db.get_anime_by_id(anime_id)
        if anime:
            await callback.message.answer(
                texts.ADDING_FINISHED.format(title=anime.title, count=len(anime.episodes)),
                reply_markup=admin_kb.admin_menu_kb()
            )
    await state.clear()
    await callback.answer()


# ── MAVJUD ANIMEGA QISM ──
@router.message(F.text == texts.ADMIN_MENU_ADD_EP, IsAdmin())
async def admin_add_ep(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(texts.ASK_ANIME_CODE_FOR_EP, reply_markup=user_kb.cancel_kb())
    await state.set_state(AdminStates.waiting_anime_code_for_ep)


@router.message(AdminStates.waiting_anime_code_for_ep)
async def admin_code_for_ep(message: Message, state: FSMContext):
    if message.text == texts.CANCEL_BTN:
        await show_admin_panel(message, state); return
    anime = await db.get_anime_by_code(message.text.strip())
    if not anime:
        results = await db.search_anime_list(message.text.strip(), limit=1)
        anime = results[0] if results else None
    if not anime:
        await message.answer(f"❌ Topilmadi: <b>{message.text}</b>"); return
    await state.update_data(anime_id=anime.id)
    await message.answer(
        texts.ANIME_FOUND_FOR_EP.format(title=anime.title, count=len(anime.episodes)),
        reply_markup=admin_kb.finish_kb()
    )
    await state.set_state(AdminStates.waiting_episodes_existing)


@router.message(AdminStates.waiting_episodes_existing, F.video)
async def admin_ep_existing(message: Message, state: FSMContext):
    data = await state.get_data()
    anime_id = data.get("anime_id")
    if not anime_id: return
    num = await db.add_episode(anime_id, message.video.file_id, message.caption or "")
    await message.answer(texts.EPISODE_ADDED.format(num=num), reply_markup=admin_kb.finish_kb())


# ── Tezkor qism qo'shish (ro'yxatdan) ──
@router.callback_query(F.data.startswith("aquick_ep:"))
async def aquick_ep(callback: CallbackQuery, state: FSMContext):
    if not await is_admin_async(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True); return
    anime_id = int(callback.data.split(":")[1])
    anime = await db.get_anime_by_id(anime_id)
    if not anime:
        await callback.answer("Topilmadi"); return
    await state.update_data(anime_id=anime_id)
    await callback.message.answer(
        texts.ANIME_FOUND_FOR_EP.format(title=anime.title, count=len(anime.episodes)),
        reply_markup=admin_kb.finish_kb()
    )
    await state.set_state(AdminStates.waiting_episodes_existing)
    await callback.answer()


# ── NOMNI O'ZGARTIRISH ──
@router.callback_query(F.data.startswith("arename:"))
async def arename(callback: CallbackQuery, state: FSMContext):
    if not await is_admin_async(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True); return
    anime_id = int(callback.data.split(":")[1])
    await state.update_data(rename_anime_id=anime_id)
    await callback.message.answer("✏️ Yangi nomni yozing:")
    await state.set_state(AdminStates.waiting_rename)
    await callback.answer()


@router.message(AdminStates.waiting_rename)
async def process_rename(message: Message, state: FSMContext):
    if not await is_admin_async(message.from_user.id): return
    data = await state.get_data()
    anime_id = data.get("rename_anime_id")
    if not anime_id: return
    await db.update_anime_title(anime_id, message.text.strip())
    await state.clear()
    anime = await db.get_anime_by_id(anime_id)
    await message.answer(f"✅ Nom o'zgartirildi: <b>{anime.title}</b>", reply_markup=admin_kb.admin_menu_kb())


# ── TAVSIF QO'SHISH ──
@router.callback_query(F.data.startswith("adesc:"))
async def adesc_start(callback: CallbackQuery, state: FSMContext):
    if not await is_admin_async(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True); return
    anime_id = int(callback.data.split(":")[1])
    await state.update_data(desc_anime_id=anime_id)
    await callback.message.answer(texts.ASK_DESCRIPTION, reply_markup=admin_kb.skip_kb())
    await state.set_state(AdminStates.waiting_description)
    await callback.answer()


@router.message(AdminStates.waiting_description)
async def process_description(message: Message, state: FSMContext):
    if not await is_admin_async(message.from_user.id): return
    if message.text == texts.CANCEL_BTN:
        await show_admin_panel(message, state); return
    data = await state.get_data()
    anime_id = data.get("desc_anime_id")
    if anime_id and message.text != texts.SKIP_BTN:
        await db.update_anime_description(anime_id, message.text.strip())
        await message.answer(texts.DESCRIPTION_SAVED, reply_markup=admin_kb.admin_menu_kb())
    else:
        await show_admin_panel(message, state); return
    await state.clear()


# ── MUQOVA QO'SHISH ──
@router.callback_query(F.data.startswith("acover:"))
async def acover_start(callback: CallbackQuery, state: FSMContext):
    if not await is_admin_async(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True); return
    anime_id = int(callback.data.split(":")[1])
    await state.update_data(cover_anime_id=anime_id)
    await callback.message.answer(texts.ASK_COVER, reply_markup=admin_kb.skip_kb())
    await state.set_state(AdminStates.waiting_cover)
    await callback.answer()


@router.message(AdminStates.waiting_cover, F.photo)
async def process_cover(message: Message, state: FSMContext):
    if not await is_admin_async(message.from_user.id): return
    data = await state.get_data()
    anime_id = data.get("cover_anime_id")
    if anime_id:
        await db.update_anime_cover(anime_id, message.photo[-1].file_id)
        await message.answer(texts.COVER_SAVED, reply_markup=admin_kb.admin_menu_kb())
    await state.clear()


@router.message(AdminStates.waiting_cover)
async def process_cover_text(message: Message, state: FSMContext):
    if not await is_admin_async(message.from_user.id): return
    if message.text == texts.CANCEL_BTN or message.text == texts.SKIP_BTN:
        await show_admin_panel(message, state); return
    await message.answer("🖼 Iltimos, rasm (photo) yuboring, matn emas.")


# ── RO'YXAT ──
@router.message(F.text == texts.ADMIN_MENU_LIST, IsAdmin())
async def admin_list(message: Message, state: FSMContext):
    await state.clear()
    anime_list = await db.list_all_anime()
    if not anime_list:
        await message.answer("Hali animelar yo'q."); return
    await message.answer(
        f"📋 Jami <b>{len(anime_list)}</b> ta anime:",
        reply_markup=admin_kb.anime_list_kb(anime_list, 0)
    )


@router.callback_query(F.data.startswith("alist:"))
async def alist_page(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    anime_list = await db.list_all_anime()
    await callback.message.edit_reply_markup(reply_markup=admin_kb.anime_list_kb(anime_list, page))
    await callback.answer()


@router.callback_query(F.data.startswith("admin_view:"))
async def admin_view(callback: CallbackQuery):
    anime_id = int(callback.data.split(":")[1])
    anime = await db.get_anime_by_id(anime_id)
    if not anime:
        await callback.answer("Topilmadi", show_alert=True); return
    text = (
        f"🎬 <b>{anime.title}</b>\n"
        f"🔢 Kod: <code>{anime.code}</code>\n"
        f"📺 Qismlar: <b>{len(anime.episodes)}</b> ta\n"
        f"🔍 Qidirilgan: {anime.search_count} marta\n"
        f"👍 {anime.likes}  👎 {anime.dislikes}\n"
        f"📝 Tavsif: {anime.description or 'yo\u02bbq'}\n"
        f"🖼 Muqova: {'✅ bor' if anime.cover_file_id else '❌ yo\u02bbq'}"
    )
    await callback.message.answer(text, reply_markup=admin_kb.anime_manage_kb(anime))
    await callback.answer()


@router.callback_query(F.data.startswith("admin_del:"))
async def admin_del_confirm(callback: CallbackQuery):
    anime_id = int(callback.data.split(":")[1])
    anime = await db.get_anime_by_id(anime_id)
    if not anime:
        await callback.answer("Topilmadi"); return
    await callback.message.answer(
        f"⚠️ <b>{anime.title}</b> va barcha qismlari o'chiriladi. Tasdiqlaysizmi?",
        reply_markup=admin_kb.confirm_delete_kb(anime_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_del:"))
async def admin_del(callback: CallbackQuery):
    anime_id = int(callback.data.split(":")[1])
    await db.delete_anime(anime_id)
    await callback.message.answer("🗑 O'chirildi!", reply_markup=admin_kb.admin_menu_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("admin_list_back:"))
async def admin_list_back(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    anime_list = await db.list_all_anime()
    await callback.message.answer(
        f"📋 Jami <b>{len(anime_list)}</b> ta anime:",
        reply_markup=admin_kb.anime_list_kb(anime_list, page)
    )
    await callback.answer()


# ── KANALLAR ──
@router.message(F.text == texts.ADMIN_MENU_CHANNELS, IsAdmin())
async def admin_channels(message: Message, state: FSMContext):
    await state.clear()
    channels = await db.get_all_channels()
    sub_on = await db.is_mandatory_sub_on()
    await message.answer("⛩️ Kanallar boshqaruvi:", reply_markup=admin_kb.channels_manage_kb(channels, sub_on))


@router.callback_query(F.data == "toggle_sub")
async def toggle_sub(callback: CallbackQuery):
    if not await is_admin_async(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True); return
    current = await db.is_mandatory_sub_on()
    await db.set_setting("mandatory_sub", "off" if current else "on")
    channels = await db.get_all_channels()
    await callback.message.edit_reply_markup(
        reply_markup=admin_kb.channels_manage_kb(channels, not current)
    )
    await callback.answer("✅ O'zgartirildi!")


@router.callback_query(F.data == "add_channel")
async def add_channel_start(callback: CallbackQuery, state: FSMContext):
    if not await is_admin_async(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True); return
    await callback.message.answer(texts.ASK_CHANNEL_ID, reply_markup=user_kb.cancel_kb())
    await state.set_state(AdminStates.waiting_channel_id)
    await callback.answer()


@router.message(AdminStates.waiting_channel_id)
async def add_ch_id(message: Message, state: FSMContext):
    if message.text == texts.CANCEL_BTN:
        await show_admin_panel(message, state); return
    await state.update_data(chat_id=message.text.strip())
    await message.answer(texts.ASK_CHANNEL_TITLE)
    await state.set_state(AdminStates.waiting_channel_title)


@router.message(AdminStates.waiting_channel_title)
async def add_ch_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer(texts.ASK_CHANNEL_URL)
    await state.set_state(AdminStates.waiting_channel_url)


@router.message(AdminStates.waiting_channel_url)
async def add_ch_url(message: Message, state: FSMContext):
    data = await state.get_data()
    await db.add_channel(data["chat_id"], data["title"], message.text.strip())
    await state.clear()
    await message.answer(texts.CHANNEL_ADDED, reply_markup=admin_kb.admin_menu_kb())


@router.callback_query(F.data.startswith("del_channel:"))
async def del_channel(callback: CallbackQuery):
    if not await is_admin_async(callback.from_user.id):
        await callback.answer(texts.NOT_ADMIN, show_alert=True); return
    await db.delete_channel(int(callback.data.split(":")[1]))
    channels = await db.get_all_channels()
    sub_on = await db.is_mandatory_sub_on()
    await callback.message.edit_reply_markup(reply_markup=admin_kb.channels_manage_kb(channels, sub_on))
    await callback.answer("🗑 O'chirildi!")


# ── BROADCAST (endi bloklaganlarni avtomatik chiqaradi) ──
@router.message(F.text == texts.ADMIN_MENU_BROADCAST, IsAdmin())
async def admin_broadcast(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(texts.ASK_BROADCAST_TEXT, reply_markup=user_kb.cancel_kb())
    await state.set_state(AdminStates.waiting_broadcast_text)


@router.message(AdminStates.waiting_broadcast_text)
async def do_broadcast(message: Message, state: FSMContext):
    if message.text == texts.CANCEL_BTN:
        await show_admin_panel(message, state); return
    await state.clear()
    await message.answer(texts.BROADCAST_STARTED)
    uids = await db.all_user_ids()
    ok, fail, blocked = 0, 0, 0
    for uid in uids:
        try:
            await message.copy_to(uid); ok += 1
        except Exception as e:
            fail += 1
            err = str(e).lower()
            if "blocked" in err or "deactivated" in err or "chat not found" in err:
                await db.mark_user_blocked(uid)
                blocked += 1
            logger.warning("Broadcast xato uid=%s: %s", uid, e)
        await asyncio.sleep(0.05)
    await message.answer(
        texts.BROADCAST_DONE.format(success=ok, fail=fail, blocked=blocked),
        reply_markup=admin_kb.admin_menu_kb()
    )


# ── MUROJAATLAR ──
@router.message(F.text == texts.ADMIN_MENU_FEEDBACK, IsAdmin())
async def admin_feedback(message: Message, state: FSMContext):
    await state.clear()
    count = await db.count_feedback()
    await message.answer(
        f"✉️ Jami <b>{count}</b> ta murojaat kelgan.\n"
        f"Har yangi murojaat avtomatik sizga forward qilinadi. 🌸"
    )


# ── PREMIUM SO'ROVLAR ──
@router.message(F.text == texts.ADMIN_MENU_PREMIUM, IsAdmin())
async def admin_premium(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "💎 Premium boshqaruvi\n\n"
        "Foydalanuvchi ID sini va muddatini yuboring:\n"
        "Masalan: <code>premium_on 123456789 2025-12-31</code>\n"
        "O'chirish: <code>premium_off 123456789</code>"
    )


@router.message(F.text.startswith("premium_on "), IsAdmin())
async def set_premium_on(message: Message, bot: Bot):
    parts = message.text.split()
    if len(parts) < 2: return
    try:
        uid = int(parts[1])
    except ValueError:
        await message.answer("❌ ID noto'g'ri, faqat raqam bo'lishi kerak."); return
    until = parts[2] if len(parts) > 2 else ""
    await db.set_user_premium(uid, True, until)
    await message.answer(f"✅ {uid} ga Premium berildi (muddat: {until or 'cheksiz'})")
    try:
        await bot.send_message(uid, f"🎉 Sizga <b>Premium</b> faollashtirildi! {f'Muddat: {until}' if until else ''} Enjoy! 💎")
    except Exception: pass


@router.message(F.text.startswith("premium_off "), IsAdmin())
async def set_premium_off(message: Message):
    parts = message.text.split()
    if len(parts) < 2: return
    try:
        uid = int(parts[1])
    except ValueError:
        await message.answer("❌ ID noto'g'ri, faqat raqam bo'lishi kerak."); return
    await db.set_user_premium(uid, False)
    await message.answer(f"✅ {uid} dan Premium olindi.")


# ── STATISTIKA ──
@router.message(F.text == texts.ADMIN_MENU_STATS, IsAdmin())
async def admin_stats(message: Message, state: FSMContext):
    await state.clear()
    users = await db.count_users()
    today = await db.count_users_today()
    premium = await db.count_premium_users()
    anime_c, ep_c = await db.count_anime_and_episodes()
    likes, dislikes = await db.total_likes_dislikes()
    fb = await db.count_feedback()
    sub_on = await db.is_mandatory_sub_on()
    channels = await db.get_all_channels()
    top = await db.top_anime(5)
    top_list = "\n".join([f"{i}. {a.title} — {a.search_count} marta" for i, a in enumerate(top, 1)]) or "Hali yo'q"
    await message.answer(texts.STATS_TEXT.format(
        users=users, today=today, premium=premium,
        anime=anime_c, episodes=ep_c,
        likes=likes, dislikes=dislikes, feedback=fb,
        sub_status="🟢 Yoq" if sub_on else "🔴 O'ch",
        channels=len(channels), top_list=top_list
    ))


# ── ADMINLAR BOSHQARUVI ──
@router.message(F.text == texts.ADMIN_MENU_ADMINS, IsAdmin())
async def admins_panel(message: Message, state: FSMContext):
    await state.clear()
    db_admins = await db.list_admins()
    await message.answer(
        "🛡 <b>Adminlar ro'yxati</b>\n\n"
        "👑 — bosh adminlar (.env orqali, bu yerdan o'chirilmaydi)\n"
        "🗑 — bazadagi adminlar (bosh admin o'chira oladi)",
        reply_markup=admin_kb.admins_manage_kb(config.SUPER_ADMIN_IDS, db_admins)
    )


@router.callback_query(F.data == "add_admin_start", IsSuperAdmin())
async def add_admin_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(texts.ASK_ADD_ADMIN_ID, reply_markup=user_kb.cancel_kb())
    await state.set_state(AdminStates.waiting_add_admin)
    await callback.answer()


@router.callback_query(F.data == "add_admin_start")
async def add_admin_start_denied(callback: CallbackQuery):
    await callback.answer(texts.NOT_SUPER_ADMIN, show_alert=True)


@router.message(AdminStates.waiting_add_admin, IsSuperAdmin())
async def add_admin_process(message: Message, state: FSMContext, bot: Bot):
    if message.text == texts.CANCEL_BTN:
        await show_admin_panel(message, state); return
    try:
        uid = int(message.text.strip())
    except ValueError:
        await message.answer("❌ ID noto'g'ri, faqat raqam yuboring."); return
    full_name = ""
    try:
        chat = await bot.get_chat(uid)
        full_name = chat.full_name or ""
    except Exception:
        pass
    added = await db.add_admin(uid, full_name, message.from_user.id)
    await state.clear()
    if added:
        await message.answer(texts.ADMIN_ADDED.format(uid=uid), reply_markup=admin_kb.admin_menu_kb())
        try:
            await bot.send_message(uid, "🎉 Sizga bot boshqaruvida <b>admin</b> huquqi berildi! /admin buyrug'ini yuboring.")
        except Exception:
            pass
    else:
        await message.answer(texts.ADMIN_ALREADY.format(uid=uid), reply_markup=admin_kb.admin_menu_kb())


@router.callback_query(F.data.startswith("rm_admin:"), IsSuperAdmin())
async def remove_admin_cb(callback: CallbackQuery):
    uid = int(callback.data.split(":")[1])
    removed = await db.remove_admin(uid)
    text = texts.ADMIN_REMOVED.format(uid=uid) if removed else texts.ADMIN_NOT_FOUND_TO_REMOVE.format(uid=uid)
    db_admins = await db.list_admins()
    await callback.message.edit_text(
        "🛡 <b>Adminlar ro'yxati</b>\n\n" + text,
        reply_markup=admin_kb.admins_manage_kb(config.SUPER_ADMIN_IDS, db_admins)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rm_admin:"))
async def remove_admin_cb_denied(callback: CallbackQuery):
    await callback.answer(texts.NOT_SUPER_ADMIN, show_alert=True)

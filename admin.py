import asyncio
import logging
import datetime

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import config, crud, admin_kb
from states import AdminStates
from filters import IsAdmin, IsSuperAdmin, is_admin_async, has_permission

router = Router()
logger = logging.getLogger("yuki_bot")

CANCEL = "❌ Bekor qilish"
SKIP = "➡️ Skip"


async def deny(target, perm_label: str):
    text = f"⛔️ Sizga '{perm_label}' bo'limi uchun ruxsat berilmagan."
    if isinstance(target, CallbackQuery):
        await target.answer(text, show_alert=True)
    else:
        await target.answer(text)


# ══════════════════════ ASOSIY PANEL ══════════════════════

@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    if not await is_admin_async(message.from_user.id):
        return
    await state.clear()
    await message.answer(
        "⛩ <b>Admin paneli</b> — Okaerinasai, Yaratuvchi-sama!\n\n"
        "Quyidagi bo'limlardan birini tanlang 👇",
        reply_markup=admin_kb.admin_panel_kb()
    )


@router.message(F.text == "❌ Bekor qilish", IsAdmin())
async def admin_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_kb.admin_panel_kb())


@router.message(F.text == "🔄 /start", IsAdmin())
async def admin_quick_start(message: Message, state: FSMContext):
    """Admin panel ichidan chiqmasdan, oddiy foydalanuvchi ko'radigan /start ekranini sinab ko'rish."""
    from start import WELCOME_TEXT
    from main_menu import main_menu_kb
    await state.clear()
    await message.answer(
        WELCOME_TEXT.format(name=message.from_user.full_name),
        reply_markup=await main_menu_kb()
    )


# ══════════════════════ ⛩ KANALLAR ══════════════════════

@router.message(F.text == "⛩ Kanallar", IsAdmin())
async def channels_menu(message: Message, state: FSMContext):
    if not await has_permission(message.from_user.id, "channels"):
        await deny(message, "Kanallar"); return
    await state.clear()
    channels = await crud.get_all_channels()
    text = "⛩ <b>Majburiy obuna kanallari</b>\n\n" + (
        "Hozircha kanal qo'shilmagan — botga kirish cheklanmagan." if not channels
        else "Kanalni o'chirish uchun ustiga bosing."
    )
    await message.answer(text, reply_markup=admin_kb.channels_kb(channels))


@router.callback_query(F.data == "ch_add")
async def ch_add_start(callback: CallbackQuery, state: FSMContext):
    if not await has_permission(callback.from_user.id, "channels"):
        await deny(callback, "Kanallar"); return
    await callback.message.answer(
        "🆔 Kanal ID sini yuboring (masalan: <code>-1001234567890</code> yoki <code>@kanal_username</code>):",
        reply_markup=admin_kb.cancel_kb()
    )
    await state.set_state(AdminStates.waiting_channel_id)
    await callback.answer()


@router.message(AdminStates.waiting_channel_id)
async def ch_add_id(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await admin_cancel(message, state); return
    await state.update_data(chat_id=message.text.strip())
    await message.answer("📝 Kanal nomini yuboring:")
    await state.set_state(AdminStates.waiting_channel_title)


@router.message(AdminStates.waiting_channel_title)
async def ch_add_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer("🔗 Kanal havolasini yuboring (masalan: https://t.me/kanal):")
    await state.set_state(AdminStates.waiting_channel_url)


@router.message(AdminStates.waiting_channel_url)
async def ch_add_url(message: Message, state: FSMContext):
    data = await state.get_data()
    await crud.add_channel(data["chat_id"], data["title"], message.text.strip())
    await state.clear()
    await message.answer("✅ Kanal qo'shildi!", reply_markup=admin_kb.admin_panel_kb())


@router.callback_query(F.data.startswith("ch_del:"))
async def ch_del(callback: CallbackQuery):
    if not await has_permission(callback.from_user.id, "channels"):
        await deny(callback, "Kanallar"); return
    await crud.delete_channel(int(callback.data.split(":")[1]))
    channels = await crud.get_all_channels()
    await callback.message.edit_reply_markup(reply_markup=admin_kb.channels_kb(channels))
    await callback.answer("🗑 O'chirildi!")


# ══════════════════════ 🎬 ANIMELAR ══════════════════════

@router.message(F.text == "🎬 Animelar", IsAdmin())
async def anime_menu(message: Message, state: FSMContext):
    if not await has_permission(message.from_user.id, "anime"):
        await deny(message, "Animelar"); return
    await state.clear()
    await message.answer("✨ Anime bo'limiga xush kelibsiz, birini tanlang:", reply_markup=admin_kb.anime_menu_kb())


@router.callback_query(F.data == "am_new")
async def am_new_start(callback: CallbackQuery, state: FSMContext):
    if not await has_permission(callback.from_user.id, "anime"):
        await deny(callback, "Animelar"); return
    await callback.message.answer("🎬 Anime nomini yuboring:", reply_markup=admin_kb.cancel_kb())
    await state.set_state(AdminStates.waiting_new_title)
    await callback.answer()


@router.message(AdminStates.waiting_new_title)
async def am_new_title(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await admin_cancel(message, state); return
    await state.update_data(title=message.text.strip())
    await message.answer(
        "📝 Tavsif yozing. Xohlasangiz, muqova rasmini ham yuborishingiz mumkin "
        "(rasmni tavsif bilan birga, rasm ostiga yozib yuboring). "
        "O'tkazib yuborish uchun Skip bosing:",
        reply_markup=admin_kb.skip_kb()
    )
    await state.set_state(AdminStates.waiting_new_description)


async def _create_anime_and_prompt_episodes(message: Message, state: FSMContext, title: str, description: str, cover_file_id: str = ""):
    code = await crud.get_next_code()
    anime = await crud.add_anime(code=code, title=title, description=description)
    if cover_file_id:
        await crud.update_anime_cover(anime.id, cover_file_id)
    await state.update_data(anime_id=anime.id, part_number=1)
    await message.answer(
        f"✅ <b>{anime.title}</b> yaratildi! Kod: <code>{anime.code}</code>\n\n"
        f"🎥 Endi 1-qism videosini yuboring (har video ketma-ket, tugagach '✅ Tugatish' yozing):",
        reply_markup=admin_kb.cancel_kb()
    )
    await state.set_state(AdminStates.waiting_episodes)


@router.message(AdminStates.waiting_new_description, F.photo)
async def am_new_desc_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    description = (message.caption or "").strip()
    await _create_anime_and_prompt_episodes(message, state, data["title"], description, message.photo[-1].file_id)


@router.message(AdminStates.waiting_new_description)
async def am_new_desc(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await admin_cancel(message, state); return
    description = "" if message.text == SKIP else message.text.strip()
    data = await state.get_data()
    await _create_anime_and_prompt_episodes(message, state, data["title"], description)


@router.message(AdminStates.waiting_episodes, F.video)
async def am_new_ep_video(message: Message, state: FSMContext):
    data = await state.get_data()
    anime_id, part = data["anime_id"], data.get("part_number", 1)
    await crud.add_episode(anime_id, part, message.video.file_id)
    await state.update_data(part_number=part + 1)
    await message.answer(f"✅ {part}-qism qo'shildi. Davom eting yoki '✅ Tugatish' deb yozing.")


@router.message(AdminStates.waiting_episodes, F.text.in_(["✅ Tugatish", CANCEL]))
async def am_new_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    anime_id = data.get("anime_id")
    await state.clear()
    anime = await crud.get_anime_by_id(anime_id) if anime_id else None
    if anime:
        episodes = await crud.get_episodes(anime.id)
        await message.answer(
            f"🎉 <b>{anime.title}</b> tayyor! Jami {len(episodes)} qism, kod: <code>{anime.code}</code>",
            reply_markup=admin_kb.admin_panel_kb()
        )
    else:
        await message.answer("Bekor qilindi.", reply_markup=admin_kb.admin_panel_kb())


@router.callback_query(F.data == "am_add_ep")
async def am_add_ep_start(callback: CallbackQuery, state: FSMContext):
    if not await has_permission(callback.from_user.id, "anime"):
        await deny(callback, "Animelar"); return
    await callback.message.answer("🔢 Qism qo'shmoqchi bo'lgan anime kodini yuboring:", reply_markup=admin_kb.cancel_kb())
    await state.set_state(AdminStates.waiting_code_for_ep)
    await callback.answer()


@router.message(AdminStates.waiting_code_for_ep)
async def am_add_ep_code(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await admin_cancel(message, state); return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam (kod) yuboring."); return
    anime = await crud.get_anime_by_code(int(message.text.strip()))
    if not anime:
        await message.answer("❌ Bunday kod topilmadi."); return
    episodes = await crud.get_episodes(anime.id)
    next_part = (episodes[-1].part_number + 1) if episodes else 1
    await state.update_data(anime_id=anime.id, part_number=next_part)
    await message.answer(
        f"🎬 <b>{anime.title}</b> — hozir {len(episodes)} qism bor.\n"
        f"🎥 {next_part}-qism videosini yuboring:",
        reply_markup=admin_kb.cancel_kb()
    )
    await state.set_state(AdminStates.waiting_episodes_existing)


@router.message(AdminStates.waiting_episodes_existing, F.video)
async def am_add_ep_video(message: Message, state: FSMContext):
    data = await state.get_data()
    anime_id, part = data["anime_id"], data.get("part_number", 1)
    await crud.add_episode(anime_id, part, message.video.file_id)
    await state.update_data(part_number=part + 1)
    await message.answer(f"✅ {part}-qism qo'shildi. Davom eting yoki '✅ Tugatish' deb yozing.")


@router.message(AdminStates.waiting_episodes_existing, F.text.in_(["✅ Tugatish", CANCEL]))
async def am_add_ep_finish(message: Message, state: FSMContext):
    await am_new_finish(message, state)


@router.callback_query(F.data.startswith("am_list:"))
async def am_list(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    anime_list = await crud.list_all_anime()
    if not anime_list:
        await callback.answer("Hali animelar yo'q.", show_alert=True); return
    text = f"📋 Jami <b>{len(anime_list)}</b> ta anime:"
    try:
        await callback.message.edit_text(text, reply_markup=admin_kb.anime_list_admin_kb(anime_list, page))
    except Exception:
        await callback.message.answer(text, reply_markup=admin_kb.anime_list_admin_kb(anime_list, page))
    await callback.answer()


@router.callback_query(F.data.startswith("am_view:"))
async def am_view(callback: CallbackQuery):
    anime_id = int(callback.data.split(":")[1])
    anime = await crud.get_anime_by_id(anime_id)
    if not anime:
        await callback.answer("Topilmadi", show_alert=True); return
    episodes = await crud.get_episodes(anime.id)
    await callback.message.answer(
        f"🎬 <b>{anime.title}</b>\n"
        f"🔢 Kod: <code>{anime.code}</code>\n"
        f"📺 Qismlar: {len(episodes)} ta\n"
        f"⬇️ Yuklab olishlar: {anime.downloads}\n"
        f"📝 Tavsif: {anime.description or 'yo\u02bbq'}\n"
        f"🖼 Muqova: {'✅ bor' if anime.cover_file_id else '❌ yo\u02bbq'}",
        reply_markup=admin_kb.anime_edit_actions_kb(anime.id)
    )
    await callback.answer()


# ── Tahrirlash (kod orqali kirish) ──
@router.callback_query(F.data == "am_edit")
async def am_edit_start(callback: CallbackQuery, state: FSMContext):
    if not await has_permission(callback.from_user.id, "anime"):
        await deny(callback, "Animelar"); return
    await callback.message.answer("🔢 Tahrirlamoqchi bo'lgan anime kodini yuboring:", reply_markup=admin_kb.cancel_kb())
    await state.set_state(AdminStates.waiting_code_for_edit)
    await callback.answer()


@router.message(AdminStates.waiting_code_for_edit)
async def am_edit_code(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await admin_cancel(message, state); return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam (kod) yuboring."); return
    anime = await crud.get_anime_by_code(int(message.text.strip()))
    if not anime:
        await message.answer("❌ Bunday kod topilmadi."); return
    await state.clear()
    await message.answer(f"✏️ <b>{anime.title}</b> — nimani tahrirlaysiz?", reply_markup=admin_kb.anime_edit_actions_kb(anime.id))


@router.callback_query(F.data.startswith("aedit_title:"))
async def aedit_title_start(callback: CallbackQuery, state: FSMContext):
    anime_id = int(callback.data.split(":")[1])
    await state.update_data(edit_anime_id=anime_id)
    await callback.message.answer("✏️ Yangi nomni yuboring:", reply_markup=admin_kb.cancel_kb())
    await state.set_state(AdminStates.waiting_edit_title)
    await callback.answer()


@router.message(AdminStates.waiting_edit_title)
async def aedit_title_process(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await admin_cancel(message, state); return
    data = await state.get_data()
    await crud.update_anime_title(data["edit_anime_id"], message.text.strip())
    await state.clear()
    await message.answer("✅ Nom yangilandi!", reply_markup=admin_kb.admin_panel_kb())


@router.callback_query(F.data.startswith("aedit_desc:"))
async def aedit_desc_start(callback: CallbackQuery, state: FSMContext):
    anime_id = int(callback.data.split(":")[1])
    await state.update_data(edit_anime_id=anime_id)
    await callback.message.answer(
        "📝 Yangi tavsifni yuboring. Muqova rasmini ham o'zgartirmoqchi bo'lsangiz, "
        "rasmni tavsif bilan birga (rasm ostiga yozib) yuboring:",
        reply_markup=admin_kb.cancel_kb()
    )
    await state.set_state(AdminStates.waiting_edit_description)
    await callback.answer()


@router.message(AdminStates.waiting_edit_description, F.photo)
async def aedit_desc_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    anime_id = data["edit_anime_id"]
    await crud.update_anime_cover(anime_id, message.photo[-1].file_id)
    if message.caption:
        await crud.update_anime_description(anime_id, message.caption.strip())
    await state.clear()
    await message.answer("✅ Muqova va tavsif yangilandi!", reply_markup=admin_kb.admin_panel_kb())


@router.message(AdminStates.waiting_edit_description)
async def aedit_desc_process(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await admin_cancel(message, state); return
    data = await state.get_data()
    await crud.update_anime_description(data["edit_anime_id"], message.text.strip())
    await state.clear()
    await message.answer("✅ Tavsif yangilandi!", reply_markup=admin_kb.admin_panel_kb())


@router.callback_query(F.data.startswith("aedit_delep:"))
async def aedit_delep_start(callback: CallbackQuery, state: FSMContext):
    anime_id = int(callback.data.split(":")[1])
    await state.update_data(edit_anime_id=anime_id)
    await callback.message.answer("🔢 O'chirmoqchi bo'lgan qism raqamini yuboring:", reply_markup=admin_kb.cancel_kb())
    await state.set_state(AdminStates.waiting_code_for_delete)
    await callback.answer()


@router.message(AdminStates.waiting_code_for_delete)
async def aedit_delep_process(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await admin_cancel(message, state); return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring."); return
    data = await state.get_data()
    await crud.delete_episode(data["edit_anime_id"], int(message.text.strip()))
    await state.clear()
    await message.answer("🗑 Qism o'chirildi!", reply_markup=admin_kb.admin_panel_kb())


# ── Premium sozlash ──
@router.callback_query(F.data.startswith("aedit_premium:"))
async def aedit_premium_menu(callback: CallbackQuery):
    if not await has_permission(callback.from_user.id, "anime"):
        await deny(callback, "Animelar"); return
    anime_id = int(callback.data.split(":")[1])
    await callback.message.answer(
        "💎 Premium sozlamalarini tanlang:",
        reply_markup=admin_kb.premium_settings_kb(anime_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("aedit_premium_on:"))
async def aedit_premium_on_start(callback: CallbackQuery, state: FSMContext):
    if not await has_permission(callback.from_user.id, "anime"):
        await deny(callback, "Animelar"); return
    anime_id = int(callback.data.split(":")[1])
    await state.update_data(premium_anime_id=anime_id)
    await callback.message.answer(
        "⏳ Necha kundan keyin bu anime <b>hammaga tekin</b> bo'lib qolsin?\n"
        "Butunlay (doimiy) Premium bo'lib qolishi uchun <code>0</code> yuboring.",
        reply_markup=admin_kb.cancel_kb()
    )
    await state.set_state(AdminStates.waiting_premium_anime_days)
    await callback.answer()


@router.message(AdminStates.waiting_premium_anime_days)
async def aedit_premium_on_process(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await admin_cancel(message, state); return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam (kunlar soni) yuboring."); return
    days = int(message.text.strip())
    data = await state.get_data()
    await crud.set_anime_premium(data["premium_anime_id"], days if days > 0 else None)
    await state.clear()
    if days > 0:
        await message.answer(
            f"✅ Anime Premium qilindi. {days} kundan keyin barcha foydalanuvchilar bepul ko'ra oladi.",
            reply_markup=admin_kb.admin_panel_kb()
        )
    else:
        await message.answer("✅ Anime butunlay (doimiy) Premium qilindi.", reply_markup=admin_kb.admin_panel_kb())


@router.callback_query(F.data.startswith("aedit_premium_off:"))
async def aedit_premium_off(callback: CallbackQuery):
    if not await has_permission(callback.from_user.id, "anime"):
        await deny(callback, "Animelar"); return
    anime_id = int(callback.data.split(":")[1])
    await crud.unset_anime_premium(anime_id)
    await callback.message.answer("✅ Premium olib tashlandi — endi bu anime hammaga tekin.", reply_markup=admin_kb.admin_panel_kb())
    await callback.answer()


# ── O'chirish (anime butunlay) ──
@router.callback_query(F.data == "am_delete")
async def am_delete_start(callback: CallbackQuery, state: FSMContext):
    if not await has_permission(callback.from_user.id, "anime"):
        await deny(callback, "Animelar"); return
    await callback.message.answer("🔢 O'chirmoqchi bo'lgan anime kodini yuboring:", reply_markup=admin_kb.cancel_kb())
    await state.set_state(AdminStates.waiting_code_for_full_delete)
    await callback.answer()


@router.message(AdminStates.waiting_code_for_full_delete)
async def am_delete_code(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await admin_cancel(message, state); return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam (kod) yuboring."); return
    anime = await crud.get_anime_by_code(int(message.text.strip()))
    if not anime:
        await message.answer("❌ Bunday kod topilmadi."); return
    await state.clear()
    await message.answer(
        f"⚠️ <b>{anime.title}</b> va barcha qismlari butunlay o'chiriladi. Ishonchingiz komilmi?",
        reply_markup=admin_kb.confirm_delete_anime_kb(anime.id)
    )


@router.callback_query(F.data.startswith("adel_confirm:"))
async def am_delete_confirm(callback: CallbackQuery):
    anime_id = int(callback.data.split(":")[1])
    await crud.delete_anime(anime_id)
    await callback.message.edit_text("🗑 O'chirildi!")
    await callback.answer()


# ══════════════════════ 📢 XABARNOMA ══════════════════════

@router.message(F.text == "📢 Xabarnoma", IsAdmin())
async def broadcast_start(message: Message, state: FSMContext):
    if not await has_permission(message.from_user.id, "broadcast"):
        await deny(message, "Xabarnoma"); return
    await state.clear()
    await message.answer("📢 Barcha foydalanuvchilarga yuboriladigan xabarni yuboring:", reply_markup=admin_kb.cancel_kb())
    await state.set_state(AdminStates.waiting_broadcast)


@router.message(AdminStates.waiting_broadcast)
async def broadcast_send(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await admin_cancel(message, state); return
    await state.clear()
    await message.answer("⏳ Yuborilmoqda...")
    uids = await crud.all_user_ids()
    ok, fail, blocked = 0, 0, 0
    for uid in uids:
        try:
            await message.copy_to(uid); ok += 1
        except Exception as e:
            fail += 1
            err = str(e).lower()
            if "blocked" in err or "deactivated" in err or "chat not found" in err:
                await crud.mark_user_blocked(uid)
                blocked += 1
        await asyncio.sleep(0.05)
    await message.answer(
        f"✅ Tugadi! {ok} ta yetdi, {fail} ta xato ({blocked} tasi botni bloklagani uchun endi ro'yxatdan chiqarildi).",
        reply_markup=admin_kb.admin_panel_kb()
    )


# ══════════════════════ 👤 FOYDALANUVCHI ══════════════════════

@router.message(F.text == "👤 Foydalanuvchi", IsAdmin())
async def user_lookup_start(message: Message, state: FSMContext):
    if not await has_permission(message.from_user.id, "premium"):
        await deny(message, "Foydalanuvchi"); return
    await state.clear()
    await message.answer("🔍 Foydalanuvchi ID sini yoki @username'ini yuboring:", reply_markup=admin_kb.cancel_kb())
    await state.set_state(AdminStates.waiting_user_query)


@router.message(AdminStates.waiting_user_query)
async def user_lookup_process(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await admin_cancel(message, state); return
    user = await crud.find_user(message.text.strip())
    if not user:
        await message.answer("❌ Bunday foydalanuvchi topilmadi."); return
    prem = "✅ FAOL" if await crud.is_premium(user.tg_id) else "❌ Yo'q"
    until = user.premium_until.strftime("%Y-%m-%d") if user.premium_until else "—"
    await state.update_data(target_uid=user.tg_id)
    await message.answer(
        f"👤 <b>{user.full_name}</b> (@{user.username or 'yo\u02bbq'})\n"
        f"🆔 <code>{user.tg_id}</code>\n"
        f"💎 Premium: {prem} (muddat: {until})\n"
        f"📅 Qo'shilgan: {user.joined_at.strftime('%Y-%m-%d')}\n\n"
        f"Premium berish uchun necha kunlik bo'lishini raqam bilan yuboring (masalan: <code>30</code>):"
    )
    await state.set_state(AdminStates.waiting_premium_days)


@router.message(AdminStates.waiting_premium_days)
async def grant_premium_days(message: Message, state: FSMContext, bot: Bot):
    if message.text == CANCEL:
        await admin_cancel(message, state); return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam (kunlar soni) yuboring."); return
    days = int(message.text.strip())
    data = await state.get_data()
    uid = data.get("target_uid")
    await state.clear()
    if not uid:
        await message.answer("Xatolik, qaytadan urinib ko'ring.", reply_markup=admin_kb.admin_panel_kb()); return
    await crud.set_premium_days(uid, days)
    await message.answer(f"✅ {uid} ga {days} kunlik Premium berildi.", reply_markup=admin_kb.admin_panel_kb())
    try:
        await bot.send_message(uid, f"🎉 Sizga <b>{days} kunlik Premium</b> faollashtirildi! Enjoy 💎")
    except Exception:
        pass


# ── /premium orqali kelgan so'rovga adminning tezkor javobi ──

@router.callback_query(F.data.startswith("premgrant:"))
async def premgrant_quick(callback: CallbackQuery, bot: Bot):
    if not await has_permission(callback.from_user.id, "premium"):
        await deny(callback, "Premium"); return
    _, uid, days = callback.data.split(":")
    uid, days = int(uid), int(days)
    await crud.set_premium_days(uid, days)
    try:
        await callback.message.edit_text(
            callback.message.html_text + f"\n\n✅ <b>{days} kunlik</b> Premium berildi — {callback.from_user.full_name}",
            parse_mode="HTML"
        )
    except Exception:
        pass
    try:
        await bot.send_message(uid, f"🎉 Sizga <b>{days} kunlik Premium</b> faollashtirildi! Enjoy 💎", parse_mode="HTML")
    except Exception:
        pass
    await callback.answer("✅ Berildi")


@router.callback_query(F.data.startswith("premgrant_custom:"))
async def premgrant_custom(callback: CallbackQuery, state: FSMContext):
    if not await has_permission(callback.from_user.id, "premium"):
        await deny(callback, "Premium"); return
    uid = int(callback.data.split(":")[1])
    await state.update_data(target_uid=uid)
    await callback.message.answer(
        f"✍️ <code>{uid}</code> uchun necha kunlik Premium berishni raqam bilan yuboring:",
        reply_markup=admin_kb.cancel_kb()
    )
    await state.set_state(AdminStates.waiting_premium_days)
    await callback.answer()


@router.callback_query(F.data.startswith("premgrant_reject:"))
async def premgrant_reject(callback: CallbackQuery, bot: Bot):
    if not await has_permission(callback.from_user.id, "premium"):
        await deny(callback, "Premium"); return
    uid = int(callback.data.split(":")[1])
    try:
        await callback.message.edit_text(
            callback.message.html_text + f"\n\n❌ Rad etildi — {callback.from_user.full_name}",
            parse_mode="HTML"
        )
    except Exception:
        pass
    try:
        await bot.send_message(uid, "😔 Hozircha Premium so'rovingiz rad etildi. Batafsil uchun admin bilan bog'laning.")
    except Exception:
        pass
    await callback.answer("Rad etildi")


# ══════════════════════ 🛡 ADMINLAR ══════════════════════

@router.message(F.text == "🛡 Adminlar", IsSuperAdmin())
async def admins_menu(message: Message, state: FSMContext):
    await state.clear()
    db_admins = await crud.list_admins()
    await message.answer(
        "🛡 <b>Adminlar</b>\n\n👑 — bosh adminlar (o'zgartirilmaydi)\n⚙️ — botdan qo'shilgan adminlar (ustiga bosib huquqlarini sozlang)",
        reply_markup=admin_kb.admins_list_kb(config.ADMIN_IDS, db_admins)
    )


@router.message(F.text == "🛡 Adminlar", IsAdmin())
async def admins_menu_denied(message: Message):
    await message.answer("⛔️ Bu bo'lim faqat bosh adminlar uchun.")


@router.callback_query(F.data == "adm_add", IsSuperAdmin())
async def adm_add_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🆔 Yangi admin qilmoqchi bo'lgan foydalanuvchi ID sini yuboring:", reply_markup=admin_kb.cancel_kb())
    await state.set_state(AdminStates.waiting_add_admin_id)
    await callback.answer()


@router.message(AdminStates.waiting_add_admin_id, IsSuperAdmin())
async def adm_add_process(message: Message, state: FSMContext, bot: Bot):
    if message.text == CANCEL:
        await admin_cancel(message, state); return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat ID (raqam) yuboring."); return
    uid = int(message.text.strip())
    full_name = ""
    try:
        chat = await bot.get_chat(uid)
        full_name = chat.full_name or ""
    except Exception:
        pass
    added = await crud.add_admin(uid, full_name, message.from_user.id, permissions="")
    await state.clear()
    if added:
        admin = await crud.get_admin(uid)
        await message.answer(
            f"✅ {uid} qo'shildi. Endi unga qaysi bo'limlarga ruxsat berishni tanlang:",
            reply_markup=admin_kb.admin_permissions_kb(uid, admin.permissions)
        )
        try:
            await bot.send_message(uid, "🎉 Sizga bot boshqaruvida admin huquqi berildi! /admin buyrug'ini yuboring.")
        except Exception:
            pass
    else:
        await message.answer("⚠️ Bu foydalanuvchi allaqachon admin.", reply_markup=admin_kb.admin_panel_kb())


@router.callback_query(F.data.startswith("adm_view:"), IsSuperAdmin())
async def adm_view(callback: CallbackQuery):
    uid = int(callback.data.split(":")[1])
    admin = await crud.get_admin(uid)
    if not admin:
        await callback.answer("Topilmadi", show_alert=True); return
    await callback.message.edit_text(
        f"⚙️ <b>{admin.full_name or uid}</b> — huquqlarni sozlang:",
        reply_markup=admin_kb.admin_permissions_kb(uid, admin.permissions)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_toggle:"), IsSuperAdmin())
async def adm_toggle(callback: CallbackQuery):
    _, uid, perm = callback.data.split(":")
    uid = int(uid)
    admin = await crud.get_admin(uid)
    if not admin:
        await callback.answer("Topilmadi", show_alert=True); return
    current = set(p.strip() for p in admin.permissions.split(",") if p.strip())
    if perm in current:
        current.discard(perm)
    else:
        current.add(perm)
    new_perms = ",".join(sorted(current))
    await crud.set_admin_permissions(uid, new_perms)
    await callback.message.edit_reply_markup(reply_markup=admin_kb.admin_permissions_kb(uid, new_perms))
    await callback.answer("✅ Yangilandi")


@router.callback_query(F.data.startswith("adm_remove:"), IsSuperAdmin())
async def adm_remove(callback: CallbackQuery):
    uid = int(callback.data.split(":")[1])
    await crud.remove_admin(uid)
    db_admins = await crud.list_admins()
    await callback.message.edit_text(
        "🛡 <b>Adminlar</b>",
        reply_markup=admin_kb.admins_list_kb(config.ADMIN_IDS, db_admins)
    )
    await callback.answer("🗑 Adminlikdan olindi")


@router.callback_query(F.data == "adm_back_list", IsSuperAdmin())
async def adm_back_list(callback: CallbackQuery):
    db_admins = await crud.list_admins()
    await callback.message.edit_text(
        "🛡 <b>Adminlar</b>",
        reply_markup=admin_kb.admins_list_kb(config.ADMIN_IDS, db_admins)
    )
    await callback.answer()


# ══════════════════════ 📊 STATISTIKA / 📁 MA'LUMOTLAR ══════════════════════

@router.message(F.text == "📊 Statistika", IsAdmin())
async def stats_quick(message: Message, state: FSMContext):
    await state.clear()
    s = await crud.get_stats()
    await message.answer(
        "📊 <b>Tezkor statistika</b>\n\n"
        f"👥 Jami: {s['total_users']} ta | Bugun: +{s['today_users']}\n"
        f"💎 Premium: {s['premium_count']} ta\n"
        f"🎬 Animelar: {s['anime_count']} ta | Qismlar: {s['episode_count']} ta"
    )


@router.message(F.text == "📁 Ma'lumotlar", IsAdmin())
async def full_data(message: Message, state: FSMContext):
    await state.clear()
    s = await crud.get_stats()
    channels = await crud.get_all_channels()
    db_admins = await crud.list_admins()
    fb_count = await crud.count_feedback()
    top = await crud.get_top_animes(5)
    top_text = "\n".join([f"{i}. {a.title} — {a.downloads} yuklab olindi" for i, a in enumerate(top, 1)]) or "Hali yo'q"
    await message.answer(
        "📁 <b>To'liq ma'lumotlar</b>\n\n"
        f"👥 Foydalanuvchilar: {s['total_users']} ta (bugun +{s['today_users']})\n"
        f"💎 Premium: {s['premium_count']} ta\n"
        f"🎬 Animelar: {s['anime_count']} ta | 📺 Qismlar: {s['episode_count']} ta\n"
        f"⛩ Majburiy kanallar: {len(channels)} ta\n"
        f"🛡 Qo'shimcha adminlar: {len(db_admins)} ta\n"
        f"✉️ Murojaatlar: {fb_count} ta\n\n"
        f"🏆 <b>Top 5 anime (yuklab olishlar bo'yicha):</b>\n{top_text}"
    )


# ══════════════════════ 📝 POST TAYYORLASH ══════════════════════

def _normalize_channel_input(raw: str) -> str:
    """Foydalanuvchi turlicha formatda kiritishi mumkin — hammasini Telegram
    tushunadigan to'g'ri chat_id formatiga keltiradi. Aynan shu normalizatsiya
    yo'qligi "Bad Request: chat not found" xatosining asosiy sababi edi:
    masalan, kanal username'i @ belgisisiz yoki t.me/ havolasi ko'rinishida
    kiritilganda Telegram uni chat sifatida topa olmaydi."""
    raw = raw.strip()
    if raw.lower().startswith(("https://t.me/", "http://t.me/", "t.me/")):
        raw = raw.split("t.me/", 1)[-1]
    raw = raw.strip("/ ").split("?")[0]
    if not raw:
        return raw
    if raw.startswith("-") and raw[1:].isdigit():
        return raw  # -1001234567890 ko'rinishidagi raqamli ID
    if raw.isdigit():
        return raw  # raqam — bo'lishi mumkin, get_chat sinab ko'radi
    if raw.startswith("@"):
        return raw
    return "@" + raw  # username, lekin @ belgisi tushib qolgan


async def _show_post_channels_kb(message: Message, state: FSMContext, edit: bool = False):
    channels = await crud.get_all_post_channels()
    data = await state.get_data()
    selected = set(data.get("post_channel_ids", []))
    text = (
        "📤 Post qaysi KANAL(LAR)GA joylansin?\n\n"
        + ("Ro'yxatdan birini yoki bir nechtasini tanlang, so'ng \"✅ Joylash\" tugmasini bosing.\n\n"
           if channels else "Hozircha saqlangan kanal yo'q — yangisini qo'shing.\n\n")
        + "🗑 — kanalni ro'yxatdan butunlay o'chiradi."
    )
    kb = admin_kb.post_channels_pick_kb(channels, selected)
    if edit:
        await message.edit_text(text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)


@router.message(F.text == "📝 Post tayyorlash", IsAdmin())
async def post_start(message: Message, state: FSMContext):
    if not await has_permission(message.from_user.id, "posts"):
        await deny(message, "Post tayyorlash"); return
    await state.clear()
    await message.answer("🔢 Post qaysi anime kodiga bog'lansin? Kodni yuboring:", reply_markup=admin_kb.cancel_kb())
    await state.set_state(AdminStates.waiting_post_code)


@router.message(AdminStates.waiting_post_code)
async def post_code(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await admin_cancel(message, state); return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam (kod) yuboring."); return
    anime = await crud.get_anime_by_code(int(message.text.strip()))
    if not anime:
        await message.answer("❌ Bunday kod topilmadi."); return
    await state.update_data(post_anime_id=anime.id, post_code=anime.code, post_channel_ids=[])
    await message.answer(f"🖼 <b>{anime.title}</b> tanlandi.", reply_markup=admin_kb.admin_panel_kb())
    await _show_post_channels_kb(message, state)


@router.callback_query(F.data.startswith("postch_pick:"))
async def postch_pick(callback: CallbackQuery, state: FSMContext):
    if not await has_permission(callback.from_user.id, "posts"):
        await deny(callback, "Post tayyorlash"); return
    ch_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    selected = set(data.get("post_channel_ids", []))
    if ch_id in selected:
        selected.discard(ch_id)
    else:
        selected.add(ch_id)
    await state.update_data(post_channel_ids=list(selected))
    await _show_post_channels_kb(callback.message, state, edit=True)
    await callback.answer()


@router.callback_query(F.data.startswith("postch_del:"))
async def postch_del(callback: CallbackQuery, state: FSMContext):
    if not await has_permission(callback.from_user.id, "posts"):
        await deny(callback, "Post tayyorlash"); return
    ch_id = int(callback.data.split(":")[1])
    await crud.delete_post_channel(ch_id)
    data = await state.get_data()
    selected = set(data.get("post_channel_ids", []))
    selected.discard(ch_id)
    await state.update_data(post_channel_ids=list(selected))
    await _show_post_channels_kb(callback.message, state, edit=True)
    await callback.answer("🗑 Ro'yxatdan o'chirildi")


@router.callback_query(F.data == "postch_new")
async def postch_new(callback: CallbackQuery, state: FSMContext):
    if not await has_permission(callback.from_user.id, "posts"):
        await deny(callback, "Post tayyorlash"); return
    await callback.message.answer(
        "🆔 Yangi kanal ID yoki @username yuboring "
        "(masalan: <code>@mening_kanalim</code> yoki <code>-1001234567890</code>):",
        reply_markup=admin_kb.cancel_kb()
    )
    await state.set_state(AdminStates.waiting_post_new_channel)
    await callback.answer()


@router.message(AdminStates.waiting_post_new_channel)
async def postch_new_id(message: Message, state: FSMContext, bot: Bot):
    if message.text == CANCEL:
        await state.set_state(None)
        await message.answer("Bekor qilindi.", reply_markup=admin_kb.admin_panel_kb())
        await _show_post_channels_kb(message, state)
        return

    normalized = _normalize_channel_input(message.text)
    if not normalized:
        await message.answer("❌ Bo'sh qiymat. Qayta yuboring."); return

    # MUHIM: postni yuborishdan OLDIN get_chat bilan tekshiramiz — shu orqali
    # "chat not found" / "bot admin emas" kabi xatolar darhol, aniq sababi bilan
    # ko'rsatiladi, foydalanuvchi rasm yuborib bo'lgach xafa bo'lmaydi.
    try:
        chat = await bot.get_chat(normalized)
        member = await bot.get_chat_member(normalized, (await bot.get_me()).id)
        if member.status not in ("administrator", "creator"):
            await message.answer(
                f"⚠️ Botga ulandim, lekin bot <b>{chat.title or normalized}</b> kanalida ADMIN emas.\n"
                f"Kanal sozlamalaridan botni admin qiling va qayta urinib ko'ring."
            )
            return
    except Exception as e:
        await message.answer(
            f"❌ Bu kanalni topolmadim: <code>{normalized}</code>\n\n"
            f"Xatolik: <code>{e}</code>\n\n"
            f"Tekshiring:\n"
            f"• Kanal @username bo'lsa, @ belgisi bilan yuboring\n"
            f"• Kanal ID raqam bo'lsa, <code>-100</code> bilan boshlanishi kerak\n"
            f"• Bot o'sha kanalga ADMIN sifatida qo'shilganini tekshiring\n\n"
            f"Qayta urinib ko'ring yoki ❌ Bekor qiling."
        )
        return

    title = chat.title or (f"@{chat.username}" if chat.username else normalized)
    saved = await crud.add_or_update_post_channel(normalized, title)
    data = await state.get_data()
    selected = set(data.get("post_channel_ids", []))
    selected.add(saved.id)
    await state.update_data(post_channel_ids=list(selected))
    await state.set_state(None)
    await message.answer(f"✅ <b>{title}</b> ro'yxatga qo'shildi va tanlandi.", reply_markup=admin_kb.admin_panel_kb())
    await _show_post_channels_kb(message, state)


@router.callback_query(F.data == "postch_cancel")
async def postch_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.")
    await callback.answer()


@router.callback_query(F.data == "postch_confirm")
async def postch_confirm(callback: CallbackQuery, state: FSMContext):
    if not await has_permission(callback.from_user.id, "posts"):
        await deny(callback, "Post tayyorlash"); return
    data = await state.get_data()
    if not data.get("post_channel_ids"):
        await callback.answer("⚠️ Kamida bitta kanal tanlang!", show_alert=True); return
    await callback.message.edit_text("✅ Kanal(lar) tanlandi.")
    await callback.message.answer(
        "🖼 Endi post uchun RASM yuboring, TAVSIFNI RASM OSTIGA (caption) yozing "
        "— masalan ovoz bergan kishi, janri, tili va h.k. Xohlagan formatda yozishingiz mumkin.",
        reply_markup=admin_kb.cancel_kb()
    )
    await state.set_state(AdminStates.waiting_post_photo)
    await callback.answer()


@router.message(AdminStates.waiting_post_photo, F.photo)
async def post_photo(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    code = data.get("post_code")
    channel_ids = data.get("post_channel_ids", [])
    caption = message.caption or ""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    bot_username = (await bot.get_me()).username
    kb = InlineKeyboardBuilder()
    # MUHIM: callback_data emas, balki deep-link (url) ishlatiladi — chunki
    # kanal postidagi callback tugmasi bosilganda javob kanalning o'ziga ketadi,
    # foydalanuvchiga botni ochib animeni ko'rsatolmaydi. Deep-link esa avval
    # botni ochadi, so'ng bot avtomatik shu animeni chiqarib beradi.
    kb.button(text="🎬 Tomosha qilish", url=f"https://t.me/{bot_username}?start=anime_{code}")
    photo_file_id = message.photo[-1].file_id
    full_caption = caption + f"\n\n👁 Anime kodi: {code}"

    channels = await crud.get_post_channels_by_ids(channel_ids)
    results = []
    for ch in channels:
        try:
            # MUHIM: post bot orqali TO'G'RIDAN-TO'G'RI kanalga yuboriladi (forward emas),
            # chunki Telegram forward qilinganda inline tugmalarni olib tashlaydi.
            await bot.send_photo(
                chat_id=ch.chat_id,
                photo=photo_file_id,
                caption=full_caption,
                reply_markup=kb.as_markup(),
                parse_mode="HTML",
            )
            results.append(f"✅ {ch.title or ch.chat_id}")
        except Exception as e:
            results.append(f"❌ {ch.title or ch.chat_id} — <code>{e}</code>")

    await state.clear()
    await message.answer(
        "📊 <b>Post natijasi:</b>\n\n" + "\n".join(results),
        reply_markup=admin_kb.admin_panel_kb()
    )


@router.message(AdminStates.waiting_post_photo)
async def post_photo_wrong(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await admin_cancel(message, state); return
    await message.answer("🖼 Iltimos, rasm yuboring (caption bilan birga).")


# ══════════════════════ 💰 PUL ISHLASH (referal) ══════════════════════

@router.message(F.text == "💰 Pul ishlash", IsAdmin())
async def earn_admin_menu(message: Message, state: FSMContext):
    if not await has_permission(message.from_user.id, "earn"):
        await deny(message, "Pul ishlash"); return
    await state.clear()
    pending = await crud.list_withdraw_requests("pending")
    await message.answer(
        f"💰 <b>Pul ishlash (referal) boshqaruvi</b>\n\n"
        f"⏳ Kutilayotgan yechish so'rovlari: <b>{len(pending)}</b> ta",
        reply_markup=admin_kb.earn_admin_menu_kb()
    )


@router.callback_query(F.data == "earn_ch_list")
async def earn_ch_list(callback: CallbackQuery):
    if not await has_permission(callback.from_user.id, "earn"):
        await deny(callback, "Pul ishlash"); return
    channels = await crud.get_all_earn_channels()
    text = (
        "📋 <b>Zayavka kanallari</b>\n\n"
        + ("Kanalni o'chirish uchun ustiga bosing." if channels
           else "Hozircha kanal qo'shilmagan.")
    )
    await callback.message.answer(text, reply_markup=admin_kb.earn_channels_admin_kb(channels))
    await callback.answer()


@router.callback_query(F.data == "earn_ch_add")
async def earn_ch_add_start(callback: CallbackQuery, state: FSMContext):
    if not await has_permission(callback.from_user.id, "earn"):
        await deny(callback, "Pul ishlash"); return
    await callback.message.answer(
        "🆔 Zayavka kanal ID sini yuboring (masalan: <code>-1001234567890</code> yoki <code>@kanal_username</code>):",
        reply_markup=admin_kb.cancel_kb()
    )
    await state.set_state(AdminStates.waiting_earn_channel_id)
    await callback.answer()


@router.message(AdminStates.waiting_earn_channel_id)
async def earn_ch_add_id(message: Message, state: FSMContext, bot: Bot):
    if message.text == CANCEL:
        await admin_cancel(message, state); return
    normalized = _normalize_channel_input(message.text)
    try:
        chat = await bot.get_chat(normalized)
    except Exception as e:
        await message.answer(
            f"❌ Bu kanalni topolmadim: <code>{normalized}</code>\nXatolik: <code>{e}</code>\n\n"
            f"Qayta urinib ko'ring yoki ❌ Bekor qiling."
        )
        return
    await state.update_data(earn_chat_id=normalized, earn_title=chat.title or normalized)
    await message.answer("📝 Kanal nomini yuboring (yoki ➡️ Skip):", reply_markup=admin_kb.skip_kb())
    await state.set_state(AdminStates.waiting_earn_channel_title)


@router.message(AdminStates.waiting_earn_channel_title)
async def earn_ch_add_title(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await admin_cancel(message, state); return
    if message.text != SKIP:
        await state.update_data(earn_title=message.text.strip())
    await message.answer("🔗 Kanal havolasini yuboring (masalan: https://t.me/kanal), yoki ➡️ Skip:", reply_markup=admin_kb.skip_kb())
    await state.set_state(AdminStates.waiting_earn_channel_url)


@router.message(AdminStates.waiting_earn_channel_url)
async def earn_ch_add_url(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await admin_cancel(message, state); return
    url = "" if message.text == SKIP else message.text.strip()
    await state.update_data(earn_url=url)
    await message.answer("💵 Bitta taklif uchun necha so'm to'lanadi? (faqat raqam):", reply_markup=admin_kb.cancel_kb())
    await state.set_state(AdminStates.waiting_earn_channel_reward)


@router.message(AdminStates.waiting_earn_channel_reward)
async def earn_ch_add_reward(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await admin_cancel(message, state); return
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring."); return
    data = await state.get_data()
    reward = int(message.text.strip())
    await crud.add_earn_channel(data["earn_chat_id"], data.get("earn_title", ""), data.get("earn_url", ""), reward)
    await state.clear()
    channels = await crud.get_all_earn_channels()
    await message.answer(
        f"✅ Zayavka kanali qo'shildi! Har bir taklif uchun <b>{reward} so'm</b>.",
        reply_markup=admin_kb.admin_panel_kb()
    )
    await message.answer("📋 <b>Zayavka kanallari</b>", reply_markup=admin_kb.earn_channels_admin_kb(channels))


@router.callback_query(F.data.startswith("earn_ch_del:"))
async def earn_ch_del(callback: CallbackQuery):
    if not await has_permission(callback.from_user.id, "earn"):
        await deny(callback, "Pul ishlash"); return
    await crud.delete_earn_channel(int(callback.data.split(":")[1]))
    channels = await crud.get_all_earn_channels()
    await callback.message.edit_reply_markup(reply_markup=admin_kb.earn_channels_admin_kb(channels))
    await callback.answer("🗑 O'chirildi!")


@router.callback_query(F.data.startswith("wd_list:"))
async def wd_list(callback: CallbackQuery):
    if not await has_permission(callback.from_user.id, "earn"):
        await deny(callback, "Pul ishlash"); return
    status = callback.data.split(":")[1]
    requests = await crud.list_withdraw_requests(status)
    if not requests:
        await callback.answer("📭 Hozircha so'rov yo'q.", show_alert=True)
        return
    await callback.message.answer(
        f"💳 <b>Kutilayotgan yechish so'rovlari</b> ({len(requests)} ta)",
        reply_markup=admin_kb.withdraw_list_kb(requests)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("wd_view:"))
async def wd_view(callback: CallbackQuery):
    if not await has_permission(callback.from_user.id, "earn"):
        await deny(callback, "Pul ishlash"); return
    wr_id = int(callback.data.split(":")[1])
    wr = await crud.get_withdraw_request(wr_id)
    if not wr:
        await callback.answer("Topilmadi", show_alert=True); return
    await callback.message.answer(
        f"💳 <b>So'rov #{wr.id}</b>\n\n"
        f"👤 Foydalanuvchi: <code>{wr.tg_id}</code>\n"
        f"💵 Summa: {wr.amount} so'm\n"
        f"💳 Karta: <code>{wr.card_info}</code>\n"
        f"📌 Holat: {wr.status}",
        reply_markup=admin_kb.withdraw_view_kb(wr.id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("wd_paid:"))
async def wd_paid(callback: CallbackQuery, bot: Bot):
    if not await has_permission(callback.from_user.id, "earn"):
        await deny(callback, "Pul ishlash"); return
    wr_id = int(callback.data.split(":")[1])
    wr = await crud.set_withdraw_status(wr_id, "paid")
    if not wr:
        await callback.answer("Topilmadi", show_alert=True); return
    await callback.message.edit_text(callback.message.html_text + "\n\n✅ <b>To'landi</b>", parse_mode="HTML")
    try:
        await bot.send_message(wr.tg_id, f"✅ {wr.amount} so'mlik pul yechish so'rovingiz to'landi! Rahmat 💰")
    except Exception:
        pass
    await callback.answer("✅ Belgilandi")


@router.callback_query(F.data.startswith("wd_reject:"))
async def wd_reject(callback: CallbackQuery, bot: Bot):
    if not await has_permission(callback.from_user.id, "earn"):
        await deny(callback, "Pul ishlash"); return
    wr_id = int(callback.data.split(":")[1])
    wr = await crud.set_withdraw_status(wr_id, "rejected")
    if not wr:
        await callback.answer("Topilmadi", show_alert=True); return
    await callback.message.edit_text(callback.message.html_text + "\n\n❌ <b>Rad etildi</b> (pul balansga qaytarildi)", parse_mode="HTML")
    try:
        await bot.send_message(wr.tg_id, f"❌ {wr.amount} so'mlik pul yechish so'rovingiz rad etildi. Summa balansingizga qaytarildi.")
    except Exception:
        pass
    await callback.answer("❌ Rad etildi")

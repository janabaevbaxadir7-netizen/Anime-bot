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


# ── O'chirish (anime butunlay) ──
@router.callback_query(F.data == "am_delete")
async def am_delete_start(callback: CallbackQuery, state: FSMContext):
    if not await has_permission(callback.from_user.id, "anime"):
        await deny(callback, "Animelar"); return
    await callback.message.answer("🔢 O'chirmoqchi bo'lgan anime kodini yuboring:", reply_markup=admin_kb.cancel_kb())
    await state.set_state(AdminStates.waiting_code_for_delete)
    await callback.answer()


@router.message(AdminStates.waiting_code_for_delete, F.text.regexp(r"^\d+$"))
async def am_delete_code(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("edit_anime_id"):
        return  # bu holatni aedit_delep_process yuqorida allaqachon ushlaydi
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
    until = user.premium_until.strftime("%Y-%m-%d") if user.

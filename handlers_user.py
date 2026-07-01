import random
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import texts, config, db
from states import UserStates
import user_kb
from subscription import check_subscription

router = Router()


async def show_main_menu(message, gender):
    await message.answer(
        f"{texts.time_greeting()}\n\n🏠 Asosiy menyu, {texts.address(gender)}!",
        reply_markup=user_kb.main_menu_kb()
    )


async def gate(bot, message, state):
    """Obuna tekshiruvi — har tugma bosishda chaqiriladi"""
    ok, missing = await check_subscription(bot, message.from_user.id)
    if not ok:
        channels = await db.get_all_channels()
        await message.answer(texts.SUBSCRIBE_REQUEST, reply_markup=user_kb.subscribe_kb(channels))
        return False
    return True


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    user, new = await db.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username or "")

    # Admin bo'lsa — admin paneliga
    if message.from_user.id in config.ADMIN_IDS:
        from handlers_admin import show_admin_panel
        await show_admin_panel(message, state)
        return

    await message.answer(texts.WELCOME_INTRO)
    ok, _ = await check_subscription(bot, message.from_user.id)
    if not ok:
        channels = await db.get_all_channels()
        await message.answer(texts.SUBSCRIBE_REQUEST, reply_markup=user_kb.subscribe_kb(channels))
        return
    if not user.gender:
        await message.answer(texts.ASK_GENDER, reply_markup=user_kb.gender_kb())
        await state.set_state(UserStates.waiting_gender)
        return
    await show_main_menu(message, user.gender)


@router.message(Command("rand"))
async def cmd_rand(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    if not await gate(bot, message, state): return
    anime_list = await db.list_all_anime()
    if not anime_list:
        await message.answer(texts.NO_TOP); return
    anime = random.choice(anime_list)
    await db.increment_search_count(anime.id)
    await message.answer(
        f"🎲 Tasodifiy anime:\n\n" + texts.ANIME_FOUND.format(title=anime.title, count=len(anime.episodes)),
        reply_markup=user_kb.episodes_grid_kb(anime)
    )


@router.message(Command("last"))
async def cmd_last(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    if not await gate(bot, message, state): return
    anime_list = await db.list_all_anime()
    if not anime_list:
        await message.answer(texts.NO_TOP); return
    a = anime_list[0]
    await message.answer(
        f"🆕 Oxirgi yuklangan:\n\n" + texts.ANIME_FOUND.format(title=a.title, count=len(a.episodes)),
        reply_markup=user_kb.episodes_grid_kb(a)
    )


@router.message(Command("top"))
async def cmd_top(message: Message, state: FSMContext):
    await state.clear()
    await show_top(message)


@router.callback_query(F.data == "check_sub")
async def check_sub_cb(callback: CallbackQuery, state: FSMContext, bot: Bot):
    ok, _ = await check_subscription(bot, callback.from_user.id)
    if not ok:
        await callback.answer(texts.SUBSCRIBE_FAIL, show_alert=True); return
    await callback.message.delete()
    await callback.message.answer(texts.SUBSCRIBE_SUCCESS)
    user = await db.get_user(callback.from_user.id)
    if not user or not user.gender:
        await callback.message.answer(texts.ASK_GENDER, reply_markup=user_kb.gender_kb())
        await state.set_state(UserStates.waiting_gender)
        return
    await show_main_menu(callback.message, user.gender)


@router.callback_query(F.data.startswith("gender:"))
async def gender_chosen(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split(":")[1]
    await db.set_user_gender(callback.from_user.id, gender)
    await state.clear()
    reply = texts.GENDER_REPLY_SENPAI if gender == "senpai" else texts.GENDER_REPLY_HIME
    await callback.message.edit_text(reply)
    await show_main_menu(callback.message, gender)


# ── QIDIRUV ──
@router.message(F.text == texts.MENU_SEARCH)
async def menu_search(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    if not await gate(bot, message, state): return
    await message.answer(
        "🔍 Anime nomi yoki kodini yuboring:\n"
        "<i>Masalan: Naruto yoki 101</i>",
        reply_markup=user_kb.cancel_kb()
    )
    await state.set_state(UserStates.waiting_code)


@router.message(F.text == texts.CANCEL_BTN)
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if message.from_user.id in config.ADMIN_IDS:
        from handlers_admin import show_admin_panel
        await show_admin_panel(message, state)
    else:
        await show_main_menu(message, user.gender if user else "")


@router.message(UserStates.waiting_code)
async def process_code(message: Message, state: FSMContext):
    query = message.text.strip()
    if query == texts.CANCEL_BTN:
        await cancel_handler(message, state); return

    # Kod yoki nom bilan qidirish
    anime = None
    if query.isdigit():
        anime = await db.get_anime_by_code(query)
    if not anime:
        results = await db.search_anime_list(query, limit=5)
        if len(results) == 1:
            anime = results[0]
        elif len(results) > 1:
            # Bir nechta natija - ro'yxat ko'rsat
            await state.clear()
            kb_builder = __import__('aiogram').utils.keyboard.InlineKeyboardBuilder()
            for r in results:
                kb_builder.button(text=f"🎬 {r.title}", callback_data=f"sel_anime:{r.id}")
            kb_builder.adjust(1)
            await message.answer(
                f"🔍 <b>'{query}'</b> bo'yicha {len(results)} ta natija topildi:",
                reply_markup=kb_builder.as_markup()
            )
            user = await db.get_user(message.from_user.id)
            await show_main_menu(message, user.gender if user else "")
            return

    if not anime or not anime.episodes:
        await message.answer(texts.ANIME_NOT_FOUND); return

    await db.increment_search_count(anime.id)
    await state.clear()
    user = await db.get_user(message.from_user.id)

    if user and user.last_anime_id == anime.id and 0 < user.last_episode_num <= len(anime.episodes):
        await message.answer(texts.CONTINUE_WATCHING.format(title=anime.title, ep=user.last_episode_num))

    await message.answer(
        f"🎬 <b>{anime.title}</b>\n"
        f"📺 Jami: <b>{len(anime.episodes)} qism</b>  |  🔍 {anime.search_count}  |  👍 {anime.likes}\n\n"
        f"Qaysi qismni ko'rmoqchisan? 👇",
        reply_markup=user_kb.episodes_grid_kb(anime)
    )
    await show_main_menu(message, user.gender if user else "")


@router.callback_query(F.data.startswith("sel_anime:"))
async def select_anime(callback: CallbackQuery):
    anime_id = int(callback.data.split(":")[1])
    anime = await db.get_anime_by_id(anime_id)
    if not anime:
        await callback.answer("Topilmadi", show_alert=True); return
    await db.increment_search_count(anime.id)
    await callback.message.answer(
        f"🎬 <b>{anime.title}</b>\n"
        f"📺 Jami: <b>{len(anime.episodes)} qism</b>  |  👍 {anime.likes}\n\n"
        f"Qaysi qismni ko'rmoqchisan? 👇",
        reply_markup=user_kb.episodes_grid_kb(anime)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("eppage:"))
async def ep_page(callback: CallbackQuery):
    _, anime_id, page = callback.data.split(":")
    anime = await db.get_anime_by_id(int(anime_id))
    if not anime:
        await callback.answer(); return
    await callback.message.edit_reply_markup(reply_markup=user_kb.episodes_grid_kb(anime, int(page)))
    await callback.answer()


@router.callback_query(F.data.startswith("allep:"))
async def show_all_eps(callback: CallbackQuery):
    _, anime_id, page = callback.data.split(":")
    anime = await db.get_anime_by_id(int(anime_id))
    if not anime:
        await callback.answer("Topilmadi", show_alert=True); return
    await callback.message.answer(
        f"📋 <b>{anime.title}</b> — barcha qismlar ({len(anime.episodes)} ta):",
        reply_markup=user_kb.episodes_grid_kb(anime, int(page))
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ep:"))
async def send_episode(callback: CallbackQuery):
    _, anime_id, ep_num = callback.data.split(":")
    anime_id, ep_num = int(anime_id), int(ep_num)
    anime = await db.get_anime_by_id(anime_id)
    episode = await db.get_episode(anime_id, ep_num)
    if not anime or not episode:
        await callback.answer("Bu qism topilmadi", show_alert=True); return
    user = await db.get_user(callback.from_user.id)
    addr = texts.address(user.gender if user else "")
    total = len(anime.episodes)
    await callback.message.answer_video(
        video=episode.file_id,
        caption=texts.EPISODE_CAPTION.format(title=anime.title, ep=ep_num, total=total, addr=addr),
        reply_markup=user_kb.episode_player_kb(anime, ep_num, total)
    )
    await db.set_user_progress(callback.from_user.id, anime_id, ep_num)
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data.startswith("rate:"))
async def rate_anime_cb(callback: CallbackQuery):
    _, anime_id, kind = callback.data.split(":")
    await db.rate_anime(int(anime_id), kind == "like")
    await callback.answer(texts.RATE_THANKS)


# ── TOP ──
async def show_top(message):
    top = await db.top_anime(10)
    if not top:
        await message.answer(texts.NO_TOP); return
    text = texts.TOP_TITLE
    for i, a in enumerate(top, 1):
        ep_count = len(a.episodes) if hasattr(a, 'episodes') else 0
        text += f"{i}. <b>{a.title}</b> — <code>{a.code}</code> | {ep_count} qism | 🔍 {a.search_count}\n"
    await message.answer(text)


@router.message(F.text == texts.MENU_TOP)
async def menu_top(message: Message, state: FSMContext):
    await state.clear()
    await show_top(message)


# ── TARIX ──
@router.message(F.text == texts.MENU_HISTORY)
async def menu_history(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if not user or not user.last_anime_id:
        await message.answer(texts.NO_HISTORY); return
    anime = await db.get_anime_by_id(user.last_anime_id)
    if not anime:
        await message.answer(texts.NO_HISTORY); return
    await message.answer(
        f"📜 <b>Mening tarixim</b>\n\n"
        f"🎬 <b>{anime.title}</b>\n"
        f"▶️ {user.last_episode_num}-qismda to'xtagansiz\n\n"
        f"Davom etasizmi?",
        reply_markup=user_kb.episodes_grid_kb(anime)
    )


# ── MUROJAAT ──
@router.message(F.text == texts.MENU_FEEDBACK)
async def menu_feedback(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    addr = texts.address(user.gender if user else "")
    await message.answer(texts.FEEDBACK_ASK.format(addr=addr), reply_markup=user_kb.cancel_kb())
    await state.set_state(UserStates.waiting_feedback)


@router.message(UserStates.waiting_feedback)
async def process_feedback(message: Message, state: FSMContext, bot: Bot):
    if message.text == texts.CANCEL_BTN:
        await cancel_handler(message, state); return
    await db.add_feedback(message.from_user.id, message.from_user.full_name, message.text or "")
    user = await db.get_user(message.from_user.id)
    await message.answer(texts.FEEDBACK_THANKS.format(addr=texts.address(user.gender if user else "")))
    await state.clear()
    await show_main_menu(message, user.gender if user else "")
    for aid in config.ADMIN_IDS:
        try:
            await bot.send_message(aid, f"✉️ Yangi murojaat!\n👤 {message.from_user.full_name} ({message.from_user.id})\n\n{message.text}")
        except Exception: pass


# ── PREMIUM ──
@router.message(F.text == texts.MENU_PREMIUM)
async def menu_premium(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    admin_username = None
    if config.ADMIN_IDS:
        try:
            chat = await bot.get_chat(config.ADMIN_IDS[0])
            admin_username = chat.username
        except Exception: pass
    user = await db.get_user(message.from_user.id)
    prefix = "✅ Sizda <b>Premium</b> aktiv!\n\n" if user and user.is_premium else ""
    await message.answer(prefix + texts.PREMIUM_TEXT, reply_markup=user_kb.premium_kb(admin_username))


@router.callback_query(F.data.startswith("premium:"))
async def premium_request(callback: CallbackQuery, bot: Bot):
    plan_map = {"1": "1 oy — 25 000 so'm", "3": "3 oy — 60 000 so'm", "6": "6 oy — 110 000 so'm"}
    plan = callback.data.split(":")[1]
    plan_text = plan_map.get(plan, plan)
    user = await db.get_user(callback.from_user.id)
    await db.add_premium_request(callback.from_user.id, callback.from_user.full_name, plan_text)
    await callback.answer(texts.PREMIUM_REQUEST_SENT, show_alert=True)
    for aid in config.ADMIN_IDS:
        try:
            await bot.send_message(
                aid,
                f"💎 Premium so'rov!\n"
                f"👤 {callback.from_user.full_name} (@{callback.from_user.username or 'yoq'})\n"
                f"🆔 ID: {callback.from_user.id}\n"
                f"📦 Tarif: {plan_text}"
            )
        except Exception: pass


# ── REKLAMA ──
@router.message(F.text == texts.MENU_ADS)
async def menu_ads(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    admin_username = None
    if config.ADMIN_IDS:
        try:
            chat = await bot.get_chat(config.ADMIN_IDS[0])
            admin_username = chat.username
        except Exception: pass
    await message.answer(texts.ADS_TEXT, reply_markup=user_kb.ads_contact_kb(admin_username))

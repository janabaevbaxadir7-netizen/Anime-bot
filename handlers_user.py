from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import texts
import config
import db
from states import UserStates
import user_kb
from subscription import check_subscription

router = Router()


async def show_main_menu(message: Message, gender: str):
    text = f"{texts.time_greeting()}\n\n🏠 Asosiy menyu, {texts.address(gender)}! Nima qilamiz? 🌸"
    await message.answer(text, reply_markup=user_kb.main_menu_kb())


async def send_subscription_prompt(message: Message):
    channels = await db.get_all_channels()
    await message.answer(texts.SUBSCRIBE_REQUEST, reply_markup=user_kb.subscribe_kb(channels))


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    user, created = await db.get_or_create_user(
        message.from_user.id, message.from_user.full_name, message.from_user.username or ""
    )
    await message.answer(texts.WELCOME_INTRO)
    ok, missing = await check_subscription(bot, message.from_user.id)
    if not ok:
        await send_subscription_prompt(message)
        return
    if not user.gender:
        await message.answer(texts.ASK_GENDER, reply_markup=user_kb.gender_kb())
        await state.set_state(UserStates.waiting_gender)
        return
    await show_main_menu(message, user.gender)


@router.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    ok, missing = await check_subscription(bot, callback.from_user.id)
    if not ok:
        await callback.answer(texts.SUBSCRIBE_FAIL, show_alert=True)
        return
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


@router.message(F.text == texts.MENU_SEARCH)
async def menu_search(message: Message, state: FSMContext, bot: Bot):
    ok, _ = await check_subscription(bot, message.from_user.id)
    if not ok:
        await send_subscription_prompt(message)
        return
    await message.answer(texts.ASK_CODE)
    await state.set_state(UserStates.waiting_code)


@router.message(UserStates.waiting_code)
async def process_code(message: Message, state: FSMContext):
    code = message.text.strip()
    if not code.isdigit():
        await message.answer(texts.ASK_CODE_INVALID)
        return
    anime = await db.get_anime_by_code(code)
    if not anime or not anime.episodes:
        await message.answer(texts.ANIME_NOT_FOUND)
        return
    await db.increment_search_count(anime.id)
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if user and user.last_anime_id == anime.id and user.last_episode_num > 0:
        ep_num = user.last_episode_num
        if ep_num <= len(anime.episodes):
            await message.answer(texts.CONTINUE_WATCHING.format(title=anime.title, ep=ep_num))
    await message.answer(
        texts.ANIME_FOUND.format(title=anime.title, count=len(anime.episodes)),
        reply_markup=user_kb.episodes_grid_kb(anime)
    )


@router.callback_query(F.data.startswith("allep:"))
async def show_all_episodes(callback: CallbackQuery):
    anime_id = int(callback.data.split(":")[1])
    anime = await db.get_anime_by_id(anime_id)
    if not anime:
        await callback.answer("😢 Topilmadi...", show_alert=True)
        return
    await callback.message.answer(
        texts.ANIME_FOUND.format(title=anime.title, count=len(anime.episodes)),
        reply_markup=user_kb.episodes_grid_kb(anime)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ep:"))
async def send_episode(callback: CallbackQuery):
    _, anime_id, ep_num = callback.data.split(":")
    anime_id, ep_num = int(anime_id), int(ep_num)
    anime = await db.get_anime_by_id(anime_id)
    episode = await db.get_episode(anime_id, ep_num)
    if not anime or not episode:
        await callback.answer("😢 Bu qism topilmadi...", show_alert=True)
        return
    user = await db.get_user(callback.from_user.id)
    addr = texts.address(user.gender if user else "")
    await callback.message.answer_video(
        video=episode.file_id,
        caption=texts.EPISODE_CAPTION.format(title=anime.title, ep=ep_num, addr=addr),
        reply_markup=user_kb.episode_player_kb(anime, ep_num, len(anime.episodes))
    )
    await db.set_user_progress(callback.from_user.id, anime_id, ep_num)
    await callback.answer()


@router.callback_query(F.data.startswith("rate:"))
async def rate_anime_cb(callback: CallbackQuery):
    _, anime_id, kind = callback.data.split(":")
    await db.rate_anime(int(anime_id), kind == "like")
    await callback.answer(texts.RATE_THANKS)


@router.message(F.text == texts.MENU_TOP)
async def menu_top(message: Message):
    top = await db.top_anime(5)
    if not top:
        await message.answer(texts.NO_TOP)
        return
    text = texts.TOP_TITLE
    for i, a in enumerate(top, 1):
        text += f"{i}. <b>{a.title}</b> — kod: <code>{a.code}</code> (🔍 {a.search_count} marta)\n"
    await message.answer(text)


@router.message(F.text == texts.MENU_HISTORY)
async def menu_history(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user or not user.last_anime_id:
        await message.answer(texts.NO_HISTORY)
        return
    anime = await db.get_anime_by_id(user.last_anime_id)
    if not anime:
        await message.answer(texts.NO_HISTORY)
        return
    await message.answer(
        texts.CONTINUE_WATCHING.format(title=anime.title, ep=user.last_episode_num),
        reply_markup=user_kb.episodes_grid_kb(anime)
    )


@router.message(F.text == texts.MENU_FEEDBACK)
async def menu_feedback(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    addr = texts.address(user.gender if user else "")
    await message.answer(texts.FEEDBACK_ASK.format(addr=addr))
    await state.set_state(UserStates.waiting_feedback)


@router.message(UserStates.waiting_feedback)
async def process_feedback(message: Message, state: FSMContext, bot: Bot):
    await db.add_feedback(message.from_user.id, message.from_user.full_name, message.text or "")
    user = await db.get_user(message.from_user.id)
    addr = texts.address(user.gender if user else "")
    await message.answer(texts.FEEDBACK_THANKS.format(addr=addr))
    await state.clear()
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"✉️ Yangi maktub!\n👤 {message.from_user.full_name} (ID: {message.from_user.id})\n\n{message.text}"
            )
        except Exception:
            pass


@router.message(F.text == texts.MENU_ADS)
async def menu_ads(message: Message, bot: Bot):
    admin_username = None
    if config.ADMIN_IDS:
        try:
            chat = await bot.get_chat(config.ADMIN_IDS[0])
            admin_username = chat.username
        except Exception:
            pass
    await message.answer(texts.ADS_TEXT, reply_markup=user_kb.ads_contact_kb(admin_username))

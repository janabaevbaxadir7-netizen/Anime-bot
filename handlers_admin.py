import asyncio
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import texts
import config
import db
from states import AdminStates
import admin_kb
import user_kb

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer(texts.NOT_ADMIN)
        return
    await state.clear()
    users = await db.count_users()
    today = await db.count_users_today()
    anime_count, episodes_count = await db.count_anime_and_episodes()
    await message.answer(
        texts.ADMIN_WELCOME.format(users=users, today=today, anime=anime_count, episodes=episodes_count),
        reply_markup=admin_kb.admin_menu_kb()
    )


@router.message(F.text == texts.BACK_BTN, F.from_user.id.in_(config.ADMIN_IDS))
async def admin_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Asosiy menyu", reply_markup=user_kb.main_menu_kb())


@router.message(F.text == texts.ADMIN_MENU_ADD, F.from_user.id.in_(config.ADMIN_IDS))
async def admin_add_anime(message: Message, state: FSMContext):
    await message.answer(texts.ASK_NEW_TITLE)
    await state.set_state(AdminStates.waiting_new_title)


@router.message(AdminStates.waiting_new_title)
async def admin_new_title(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
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
async def admin_receive_episode(message: Message, state: FSMContext):
    data = await state.get_data()
    anime_id = data.get("anime_id")
    if not anime_id:
        return
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


@router.message(F.text == texts.ADMIN_MENU_ADD_EP, F.from_user.id.in_(config.ADMIN_IDS))
async def admin_add_episode_existing(message: Message, state: FSMContext):
    await message.answer(texts.ASK_ANIME_CODE_FOR_EP)
    await state.set_state(AdminStates.waiting_anime_code_for_ep)


@router.message(AdminStates.waiting_anime_code_for_ep)
async def admin_code_for_ep(message: Message, state: FSMContext):
    anime = await db.get_anime_by_code(message.text.strip())
    if not anime:
        await message.answer(texts.ANIME_NOT_FOUND)
        return
    await state.update_data(anime_id=anime.id)
    await message.answer(
        texts.ANIME_FOUND_FOR_EP.format(title=anime.title, count=len(anime.episodes)),
        reply_markup=admin_kb.finish_kb()
    )
    await state.set_state(AdminStates.waiting_episodes_existing)


@router.message(AdminStates.waiting_episodes_existing, F.video)
async def admin_receive_episode_existing(message: Message, state: FSMContext):
    data = await state.get_data()
    anime_id = data.get("anime_id")
    if not anime_id:
        return
    num = await db.add_episode(anime_id, message.video.file_id, message.caption or "")
    await message.answer(texts.EPISODE_ADDED.format(num=num), reply_markup=admin_kb.finish_kb())


@router.message(F.text == texts.ADMIN_MENU_LIST, F.from_user.id.in_(config.ADMIN_IDS))
async def admin_list_anime(message: Message):
    anime_list = await db.list_all_anime()
    if not anime_list:
        await message.answer(texts.NO_TOP)
        return
    await message.answer("📋 Barcha sarguzashtlar:", reply_markup=admin_kb.anime_list_kb(anime_list))


@router.callback_query(F.data.startswith("admin_view:"))
async def admin_view_anime(callback: CallbackQuery):
    anime_id = int(callback.data.split(":")[1])
    anime = await db.get_anime_by_id(anime_id)
    if not anime:
        await callback.answer("Topilmadi", show_alert=True)
        return
    text = (
        f"🎴 <b>{anime.title}</b>\nKod: <code>{anime.code}</code>\n"
        f"Qismlar: {len(anime.episodes)}\n🔍 Qidirilgan: {anime.search_count} marta\n"
        f"👍 {anime.likes} 👎 {anime.dislikes}"
    )
    await callback.message.answer(text, reply_markup=admin_kb.anime_manage_kb(anime))
    await callback.answer()


@router.callback_query(F.data.startswith("admin_del:"))
async def admin_delete_anime(callback: CallbackQuery):
    await db.delete_anime(int(callback.data.split(":")[1]))
    await callback.message.answer("🗑✨ O'chirildi!")
    await callback.answer()


@router.callback_query(F.data == "admin_list_back")
async def admin_list_back(callback: CallbackQuery):
    anime_list = await db.list_all_anime()
    await callback.message.answer("📋 Barcha sarguzashtlar:", reply_markup=admin_kb.anime_list_kb(anime_list))
    await callback.answer()


@router.message(F.text == texts.ADMIN_MENU_CHANNELS, F.from_user.id.in_(config.ADMIN_IDS))
async def admin_channels(message: Message):
    channels = await db.get_all_channels()
    sub_on = await db.is_mandatory_sub_on()
    await message.answer("⛩️ Torii darvozalari boshqaruvi:", reply_markup=admin_kb.channels_manage_kb(channels, sub_on))


@router.callback_query(F.data == "toggle_sub")
async def toggle_sub(callback: CallbackQuery):
    current = await db.is_mandatory_sub_on()
    await db.set_setting("mandatory_sub", "off" if current else "on")
    channels = await db.get_all_channels()
    sub_on = await db.is_mandatory_sub_on()
    await callback.message.edit_reply_markup(reply_markup=admin_kb.channels_manage_kb(channels, sub_on))
    await callback.answer("✅ Holat o'zgartirildi!")


@router.callback_query(F.data == "add_channel")
async def add_channel_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(texts.ASK_CHANNEL_ID)
    await state.set_state(AdminStates.waiting_channel_id)
    await callback.answer()


@router.message(AdminStates.waiting_channel_id)
async def add_channel_id(message: Message, state: FSMContext):
    await state.update_data(chat_id=message.text.strip())
    await message.answer(texts.ASK_CHANNEL_TITLE)
    await state.set_state(AdminStates.waiting_channel_title)


@router.message(AdminStates.waiting_channel_title)
async def add_channel_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer(texts.ASK_CHANNEL_URL)
    await state.set_state(AdminStates.waiting_channel_url)


@router.message(AdminStates.waiting_channel_url)
async def add_channel_url(message: Message, state: FSMContext):
    data = await state.get_data()
    await db.add_channel(data["chat_id"], data["title"], message.text.strip())
    await message.answer(texts.CHANNEL_ADDED, reply_markup=admin_kb.admin_menu_kb())
    await state.clear()


@router.callback_query(F.data.startswith("del_channel:"))
async def del_channel(callback: CallbackQuery):
    await db.delete_channel(int(callback.data.split(":")[1]))
    channels = await db.get_all_channels()
    sub_on = await db.is_mandatory_sub_on()
    await callback.message.edit_reply_markup(reply_markup=admin_kb.channels_manage_kb(channels, sub_on))
    await callback.answer("🗑 O'chirildi!")


@router.message(F.text == texts.ADMIN_MENU_BROADCAST, F.from_user.id.in_(config.ADMIN_IDS))
async def admin_broadcast_start(message: Message, state: FSMContext):
    await message.answer(texts.ASK_BROADCAST_TEXT)
    await state.set_state(AdminStates.waiting_broadcast_text)


@router.message(AdminStates.waiting_broadcast_text)
async def admin_broadcast_send(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(texts.BROADCAST_STARTED)
    user_ids = await db.all_user_ids()
    success, fail = 0, 0
    for uid in user_ids:
        try:
            await message.copy_to(uid)
            success += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)
    await message.answer(
        texts.BROADCAST_DONE.format(success=success, fail=fail),
        reply_markup=admin_kb.admin_menu_kb()
    )


@router.message(F.text == texts.ADMIN_MENU_FEEDBACK, F.from_user.id.in_(config.ADMIN_IDS))
async def admin_feedback(message: Message):
    count = await db.count_feedback()
    await message.answer(f"✉️ Jami {count} ta maktub keldi. (Har bir yangi maktub avtomatik sizga forward qilinadi 🌸)")


@router.message(F.text == texts.ADMIN_MENU_STATS, F.from_user.id.in_(config.ADMIN_IDS))
async def admin_stats(message: Message):
    users = await db.count_users()
    today = await db.count_users_today()
    anime_count, episodes_count = await db.count_anime_and_episodes()
    likes, dislikes = await db.total_likes_dislikes()
    feedback_count = await db.count_feedback()
    sub_on = await db.is_mandatory_sub_on()
    channels = await db.get_all_channels()
    top = await db.top_anime(5)
    top_list = "\n".join(
        [f"{i}. {a.title} ({a.search_count} marta)" for i, a in enumerate(top, 1)]
    ) or "Hali yo'q"
    await message.answer(
        texts.STATS_TEXT.format(
            users=users, today=today, anime=anime_count, episodes=episodes_count,
            likes=likes, dislikes=dislikes, feedback=feedback_count,
            sub_status="🟢 Yoqilgan" if sub_on else "🔴 O'chirilgan",
            channels=len(channels), top_list=top_list
        )
    )

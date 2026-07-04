from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from crud import (
    get_random_animes, get_top_animes, get_last_animes,
    get_anime_by_code, get_episodes, get_episode,
    increment_downloads, is_premium, save_anime_for_user,
    is_anime_currently_premium,
)
from anime_kb import anime_list_kb, episode_kb
from subscription import require_subscription_for_anime

router = Router()


@router.message(Command("rand"))
async def rand_handler(message: Message):
    animes = await get_random_animes(15)
    if not animes:
        await message.answer("😔 Hozircha bazada anime yo'q.")
        return
    await message.answer(
        "🎲 <b>Tasodifiy 15 ta Anime</b>",
        reply_markup=anime_list_kb(animes),
        parse_mode="HTML",
    )


@router.message(Command("top"))
async def top_handler(message: Message):
    animes = await get_top_animes(15)
    if not animes:
        await message.answer("😔 Hozircha bazada anime yo'q.")
        return
    await message.answer(
        "🏆 <b>TOP 15 ta Anime</b>",
        reply_markup=anime_list_kb(animes),
        parse_mode="HTML",
    )


@router.message(Command("last"))
async def last_handler(message: Message):
    animes = await get_last_animes(15)
    if not animes:
        await message.answer("😔 Hozircha bazada anime yo'q.")
        return
    await message.answer(
        "🎬 <b>Oxirgi 15 ta Anime</b>",
        reply_markup=anime_list_kb(animes),
        parse_mode="HTML",
    )


async def send_anime_card(message_or_call, anime, page: int = 0):
    """Anime kartochkasini (nomi, tavsifi, kod, yuklab olishlar, qism tugmalari) yuboradi.
    Agar muqova rasmi bo'lsa, rasm bilan birga; bo'lmasa oddiy matn sifatida yuboradi."""
    episodes = await get_episodes(anime.id)
    premium_line = ""
    if is_anime_currently_premium(anime):
        if anime.premium_free_at:
            premium_line = f"💎 Premium (tekin bo'lish sanasi: {anime.premium_free_at.strftime('%Y-%m-%d')})\n"
        else:
            premium_line = "💎 Premium anime\n"
    text = (
        f"🎬 <b>{anime.title}</b>\n\n"
        f"<i>{anime.description}</i>\n\n"
        f"👁 Anime kodi: {anime.code}\n"
        f"⬇️ Yuklab olishlar: {anime.downloads} ta\n"
        f"{premium_line}"
        f"🤖 Bot: @{(await message_or_call.bot.get_me()).username}"
    )
    kb = episode_kb(anime.code, len(episodes), bool(anime.trailer_file_id), page=page)

    target = message_or_call.message if isinstance(message_or_call, CallbackQuery) else message_or_call
    if anime.cover_file_id:
        await target.answer_photo(photo=anime.cover_file_id, caption=text, reply_markup=kb, parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("anime_"))
async def open_anime_card(call: CallbackQuery, bot: Bot, state: FSMContext):
    code = int(call.data.split("_")[1])
    anime = await get_anime_by_code(code)
    if not anime:
        await call.answer("Topilmadi", show_alert=True)
        return
    if not await require_subscription_for_anime(call.message, bot, call.from_user.id, state, code):
        await call.answer()
        return
    await send_anime_card(call, anime)
    await call.answer()


@router.callback_query(F.data.startswith("eppg_"))
async def episode_page_cb(call: CallbackQuery):
    """Qismlar ro'yxatida ← → sahifalash tugmalari bosilganda ishlaydi."""
    _, code, page = call.data.split("_")
    code, page = int(code), int(page)
    anime = await get_anime_by_code(code)
    if not anime:
        await call.answer("Topilmadi", show_alert=True)
        return
    episodes = await get_episodes(anime.id)
    kb = episode_kb(anime.code, len(episodes), bool(anime.trailer_file_id), page=page)
    try:
        await call.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass
    await call.answer()


@router.callback_query(F.data.startswith("trailer_"))
async def send_trailer(call: CallbackQuery):
    code = int(call.data.split("_")[1])
    anime = await get_anime_by_code(code)
    if not anime or not anime.trailer_file_id:
        await call.answer("Trailer topilmadi", show_alert=True)
        return
    await call.message.answer_video(
        video=anime.trailer_file_id,
        caption=f"🎥 {anime.title} — Tanishtiruv (trailer)",
    )
    await call.answer()


@router.callback_query(F.data.startswith("ep_"))
async def send_episode(call: CallbackQuery):
    _, code, part = call.data.split("_")
    code, part = int(code), int(part)

    anime = await get_anime_by_code(code)
    if not anime:
        await call.answer("Topilmadi", show_alert=True)
        return

    # Premium anime bo'lsa (va muddati hali o'tmagan bo'lsa), foydalanuvchi premium ekanini tekshiramiz
    if is_anime_currently_premium(anime) and not await is_premium(call.from_user.id):
        await call.answer(
            "💎 Bu anime faqat Premium foydalanuvchilar uchun. /premium orqali sotib oling.",
            show_alert=True,
        )
        return

    episode = await get_episode(anime.id, part)
    if not episode:
        await call.answer("Bu qism topilmadi", show_alert=True)
        return

    await call.message.answer_video(
        video=episode.file_id,
        caption=f"{anime.title} — [{part}-qism]",
    )
    await increment_downloads(anime.id)
    await call.answer()


@router.callback_query(F.data.startswith("all_"))
async def send_all_episodes(call: CallbackQuery):
    code = int(call.data.split("_")[1])
    anime = await get_anime_by_code(code)
    if not anime:
        await call.answer("Topilmadi", show_alert=True)
        return

    if is_anime_currently_premium(anime) and not await is_premium(call.from_user.id):
        await call.answer("💎 Bu anime faqat Premium foydalanuvchilar uchun.", show_alert=True)
        return

    episodes = await get_episodes(anime.id)
    for ep in episodes:
        await call.message.answer_video(
            video=ep.file_id,
            caption=f"{anime.title} — [{ep.part_number}-qism]",
        )
    await increment_downloads(anime.id)
    await call.answer("Barcha qismlar yuborildi ✅")


@router.callback_query(F.data.startswith("save_"))
async def save_anime_cb(call: CallbackQuery):
    code = int(call.data.split("_")[1])
    anime = await get_anime_by_code(code)
    if not anime:
        await call.answer("Topilmadi", show_alert=True)
        return
    added = await save_anime_for_user(call.from_user.id, code)
    if added:
        await call.answer("✅ Saqlangan animelarga qo'shildi!", show_alert=True)
    else:
        await call.answer("ℹ️ Bu anime allaqachon saqlangan.", show_alert=True)

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from crud import (
    get_random_animes, get_top_animes, get_last_animes,
    get_anime_by_code, get_episodes, get_episode,
    increment_downloads, is_premium,
)
from anime_kb import anime_list_kb, episode_kb

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


async def send_anime_card(message_or_call, anime):
    """Anime kartochkasini (nomi, tavsifi, kod, yuklab olishlar, qism tugmalari) yuboradi."""
    episodes = await get_episodes(anime.id)
    text = (
        f"🎬 <b>{anime.title}</b>\n\n"
        f"<i>{anime.description}</i>\n\n"
        f"👁 Anime kodi: {anime.code}\n"
        f"⬇️ Yuklab olishlar: {anime.downloads} ta\n"
        f"🤖 Bot: @{(await message_or_call.bot.get_me()).username}"
    )
    kb = episode_kb(anime.code, len(episodes))

    target = message_or_call.message if isinstance(message_or_call, CallbackQuery) else message_or_call
    await target.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("anime_"))
async def open_anime_card(call: CallbackQuery):
    code = int(call.data.split("_")[1])
    anime = await get_anime_by_code(code)
    if not anime:
        await call.answer("Topilmadi", show_alert=True)
        return
    await send_anime_card(call, anime)
    await call.answer()


@router.callback_query(F.data.startswith("ep_"))
async def send_episode(call: CallbackQuery):
    _, code, part = call.data.split("_")
    code, part = int(code), int(part)

    anime = await get_anime_by_code(code)
    if not anime:
        await call.answer("Topilmadi", show_alert=True)
        return

    # Premium anime bo'lsa, foydalanuvchi premium ekanini tekshiramiz
    if anime.is_premium and not await is_premium(call.from_user.id):
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

    if anime.is_premium and not await is_premium(call.from_user.id):
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

from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultCachedPhoto,
    InputTextMessageContent,
)

import crud
from anime_kb import episode_kb

router = Router()


def _build_caption(anime, episode_count: int) -> str:
    return (
        f"🎬 <b>{anime.title}</b>\n\n"
        f"<i>{anime.description}</i>\n\n"
        f"👁 Anime kodi: {anime.code}\n"
        f"⬇️ Yuklab olishlar: {anime.downloads} ta"
    )


@router.inline_query()
async def share_anime_inline(inline_query: InlineQuery):
    """"↪️ Ulashish" tugmasi bosilganda ishga tushadi (switch_inline_query orqali).
    Anime kodi bo'yicha to'liq kartochkani (rasm/matn + tugmalar bilan) qaytaradi,
    shunda foydalanuvchi tanlagan chatga ODDIY MATN emas, haqiqiy karточка yuboriladi."""
    query = inline_query.query.strip()

    if not query.isdigit():
        await inline_query.answer([], cache_time=1, is_personal=True)
        return

    anime = await crud.get_anime_by_code(int(query))
    if not anime:
        await inline_query.answer([], cache_time=1, is_personal=True)
        return

    episodes = await crud.get_episodes(anime.id)
    kb = episode_kb(anime.code, len(episodes))
    caption = _build_caption(anime, len(episodes))

    if anime.cover_file_id:
        result = InlineQueryResultCachedPhoto(
            id=str(anime.code),
            photo_file_id=anime.cover_file_id,
            caption=caption,
            parse_mode="HTML",
            reply_markup=kb,
        )
    else:
        result = InlineQueryResultArticle(
            id=str(anime.code),
            title=anime.title,
            description=f"Anime kodi: {anime.code}",
            input_message_content=InputTextMessageContent(message_text=caption, parse_mode="HTML"),
            reply_markup=kb,
        )

    await inline_query.answer([result], cache_time=5, is_personal=True)

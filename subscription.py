from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import crud
from filters import is_admin_async


def subscribe_kb(channels) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=f"➕ {ch.title or 'Kanal'}", url=ch.url)] for ch in channels if ch.url]
    rows.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def check_subscription(bot: Bot, user_id: int) -> tuple[bool, list]:
    """Barcha ro'yxatdagi kanallarga a'zoligini tekshiradi.
    Agar hech qanday kanal qo'shilmagan bo'lsa, tekshiruv o'tkazilmaydi (True qaytadi).
    Qaytariladigan ro'yxatda FAQAT hali obuna bo'linmagan kanallar bo'ladi —
    shu sabab "Tekshirish" bosilganda ro'yxat avtomatik qisqarib boradi."""
    channels = await crud.get_all_channels()
    if not channels:
        return True, []

    not_subscribed = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch.chat_id, user_id=user_id)
            if member.status in ("left", "kicked"):
                not_subscribed.append(ch)
        except Exception:
            not_subscribed.append(ch)

    return len(not_subscribed) == 0, not_subscribed


async def require_subscription_for_anime(target, bot: Bot, user_id: int, state: FSMContext, anime_code: int) -> bool:
    """Anime kartochkasini ko'rsatishdan OLDIN chaqiriladi.
    Admin yoki Premium bo'lsa — talab qilinmaydi (True).
    Aks holda, hali obuna bo'linmagan kanallar bilan xabar yuboradi, o'sha
    animening kodini state'da saqlab qo'yadi (obunadan keyin avtomatik ochilishi uchun)
    va False qaytaradi — chaqiruvchi funksiya davom etmasligi kerak."""
    if await is_admin_async(user_id) or await crud.is_premium(user_id):
        return True

    ok, channels = await check_subscription(bot, user_id)
    if ok:
        return True

    await state.update_data(pending_anime_code=anime_code)
    await target.answer(
        "⚠️ Bu animeni ko'rish uchun avval quyidagi kanal(lar)ga obuna bo'ling!",
        reply_markup=subscribe_kb(channels),
    )
    return False

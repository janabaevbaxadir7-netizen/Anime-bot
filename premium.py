from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

import config, crud
from premium_kb import premium_kb, premium_grant_kb

router = Router()

PREMIUM_TEXT = (
    "💎 <b>«PREMIUM» obunasi nima uchun kerak?</b>\n\n"
    "<blockquote>"
    "🚫 Kanallarga obuna bo'lish shart emas.\n"
    "🚫 Hech qanday reklamalarsiz.\n"
    "📈 Kerakli Animelar sifatli formatda.\n"
    "⭐️ Premium Animelarni ko'rish imkoniyati."
    "</blockquote>\n\n"
    "Pastdagi <b>«💎 Premium so'rash»</b> tugmasini bosing — so'rovingiz to'g'ridan-to'g'ri "
    "adminga yetadi va u siz bilan narx/muddat bo'yicha bog'lanadi."
)


@router.message(Command("premium"))
async def premium_handler(message: Message):
    await message.answer(PREMIUM_TEXT, reply_markup=premium_kb(), parse_mode="HTML")


async def _get_premium_admin_ids() -> set[int]:
    admin_ids = set(config.ADMIN_IDS)
    for a in await crud.list_admins():
        if "premium" in (a.permissions or ""):
            admin_ids.add(a.id)
    return admin_ids


@router.callback_query(F.data == "premium_request")
async def premium_request_cb(callback: CallbackQuery, bot: Bot):
    user = callback.from_user
    admin_ids = await _get_premium_admin_ids()
    text = (
        f"💎 <b>Yangi Premium so'rovi!</b>\n\n"
        f"👤 {user.full_name} (@{user.username or 'yo\u02bbq'})\n"
        f"🆔 <code>{user.id}</code>\n\n"
        f"Muddatni tanlang yoki shaxsan bog'laning:"
    )
    kb = premium_grant_kb(user.id)
    sent = 0
    for aid in admin_ids:
        try:
            await bot.send_message(aid, text, reply_markup=kb, parse_mode="HTML")
            sent += 1
        except Exception:
            pass
    if sent:
        await callback.answer("✅ So'rovingiz adminga yuborildi, tez orada bog'lanishadi!", show_alert=True)
    else:
        await callback.answer("⚠️ Hozircha hech kimga yetkazib bo'lmadi, birozdan keyin qayta urinib ko'ring.", show_alert=True)

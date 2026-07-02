from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from config import ADMIN_IDS
from database.requests import add_premium_request, update_request_status, set_premium
from keyboards.premium_kb import premium_kb, premium_admin_decision_kb
import datetime

router = Router()

PREMIUM_TEXT = (
    "💎 <b>«PREMIUM» obunasi nima uchun kerak?</b>\n\n"
    "<blockquote>"
    "🚫 Kanallarga obuna bo'lish shart emas.\n"
    "🚫 Hech qanday reklamalarsiz.\n"
    "📈 Kerakli Animelar sifatli formatda.\n"
    "⭐️ Premium Animelarni ko'rish imkoniyati."
    "</blockquote>"
)


@router.message(Command("premium"))
async def premium_handler(message: Message):
    await message.answer(PREMIUM_TEXT, reply_markup=premium_kb(), parse_mode="HTML")


@router.callback_query(F.data == "premium_buy")
async def premium_buy(call: CallbackQuery, bot: Bot):
    """Foydalanuvchi sotib olishni bosganda so'rov admin panelga yuboriladi."""
    req = await add_premium_request(
        tg_id=call.from_user.id,
        full_name=call.from_user.full_name,
    )
    for admin_id in ADMIN_IDS:
        await bot.send_message(
            admin_id,
            f"💎 <b>Yangi Premium so'rov</b>\n\n"
            f"👤 {call.from_user.full_name}\n"
            f"🆔 <code>{call.from_user.id}</code>",
            reply_markup=premium_admin_decision_kb(req.id, call.from_user.id),
            parse_mode="HTML",
        )
    await call.answer("✅ So'rovingiz adminga yuborildi. Tez orada javob olasiz!", show_alert=True)


@router.callback_query(F.data.startswith("premapprove_"))
async def premium_approve(call: CallbackQuery, bot: Bot):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("⛔️ Sizga ruxsat yo'q.", show_alert=True)
        return

    _, request_id, tg_id = call.data.split("_")
    request_id, tg_id = int(request_id), int(tg_id)

    until = datetime.datetime.utcnow() + datetime.timedelta(days=30)
    await set_premium(tg_id, until)
    await update_request_status(request_id, "approved")

    await bot.send_message(tg_id, "🎉 Tabriklaymiz! Sizga 30 kunlik Premium obuna faollashtirildi.")
    await call.message.edit_text(call.message.text + "\n\n✅ <b>TASDIQLANDI</b>", parse_mode="HTML")
    await call.answer("Tasdiqlandi ✅")


@router.callback_query(F.data.startswith("premreject_"))
async def premium_reject(call: CallbackQuery, bot: Bot):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("⛔️ Sizga ruxsat yo'q.", show_alert=True)
        return

    _, request_id, tg_id = call.data.split("_")
    request_id, tg_id = int(request_id), int(tg_id)

    await update_request_status(request_id, "rejected")
    await bot.send_message(tg_id, "❌ Kechirasiz, Premium so'rovingiz rad etildi.")
    await call.message.edit_text(call.message.text + "\n\n❌ <b>RAD ETILDI</b>", parse_mode="HTML")
    await call.answer("Rad etildi ❌")

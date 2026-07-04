from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

import config, crud
from states import SupportStates

router = Router()


async def help_kb() -> InlineKeyboardMarkup:
    admin_id = await crud.get_responsible_admin("help")
    rows = [[InlineKeyboardButton(text="✍️ Botdan Murojaat yozish", callback_data="fb_start")]]
    if admin_id:
        rows.append([InlineKeyboardButton(text="✈️ Admin bilan shaxsan bog'lanish", url=f"tg://user?id={admin_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "🙅 Savol va Takliflar bo'lsa pastdagi tugma orqali murojaat qilishingiz mumkin!",
        reply_markup=await help_kb(),
    )


@router.callback_query(F.data == "fb_start")
async def fb_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✍️ Murojaatingizni (savol, taklif, shikoyat) yozib yuboring:")
    await state.set_state(SupportStates.waiting_feedback_text)
    await callback.answer()


@router.message(SupportStates.waiting_feedback_text)
async def fb_receive(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    text = message.text or message.caption or "(matnsiz xabar)"
    await crud.add_feedback(message.from_user.id, message.from_user.full_name, text)
    await message.answer("✅ Murojaatingiz qabul qilindi, tez orada javob beramiz!")

    admin_ids = set(config.ADMIN_IDS)
    for a in await crud.list_admins():
        admin_ids.add(a.id)  # murojaatlar maxsus ruxsat talab qilmaydi — barcha adminlarga boradi
    for aid in admin_ids:
        try:
            await bot.send_message(
                aid,
                f"📨 <b>Yangi murojaat!</b>\n\n"
                f"👤 {message.from_user.full_name} (@{message.from_user.username or 'yo\u02bbq'})\n"
                f"🆔 <code>{message.from_user.id}</code>\n\n"
                f"💬 {text}\n\n"
                f"Javob berish uchun: <a href=\"tg://user?id={message.from_user.id}\">shaxsiy chatga o'tish</a>",
                parse_mode="HTML"
            )
        except Exception:
            pass

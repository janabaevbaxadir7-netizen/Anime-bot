from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import config

router = Router()


def help_kb() -> InlineKeyboardMarkup:
    admin_id = config.ADMIN_IDS[0] if config.ADMIN_IDS else None
    rows = []
    if admin_id:
        rows.append([InlineKeyboardButton(text="✈️ Qo'llab Quvvatlash", url=f"tg://user?id={admin_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "🙅 Savol va Takliflar bo'lsa pastdagi tugma orqali murojaat qilishingiz mumkin!",
        reply_markup=help_kb(),
    )

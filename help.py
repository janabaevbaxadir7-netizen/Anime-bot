from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import SUPPORT_CHAT

router = Router()


def help_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✈️ Qo'llab Quvvatlash", url=SUPPORT_CHAT)]
        ]
    )


@router.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "🙅 Savol va Takliflar bo'lsa pastdagi manzilimizga murojaat qilishingiz mumkin!",
        reply_markup=help_kb(),
    )

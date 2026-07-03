from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import config

router = Router()

DEV_TEXT = (
    "🧑‍💻 <b>Bot dasturchisi:</b> Baxadir\n\n"
    "❗️ <i><u>Eslatma: Bot dasturchisini bu botga hech qanday aloqasi yo'q!</u></i>\n\n"
    "💵 <b>Siz ham o'z telegram botingizni yaratib daromad qilishni boshlang!</b>\n"
    "Botlarga rasmiy ravishda avtomatik to'lov tizimlari qo'shilgan.\n\n"
    "⬇️ Sizga ham shunday turdagi bot kerak bo'lsa bizga murojaat qilishingiz mumkin!"
)


def dev_keyboard() -> InlineKeyboardMarkup:
    admin_id = config.ADMIN_IDS[0] if config.ADMIN_IDS else None
    rows = []
    if admin_id:
        rows.append([InlineKeyboardButton(text="👤 Ma'lumot olish", url=f"tg://user?id={admin_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("dev"))
async def dev_command(message: Message):
    await message.answer(DEV_TEXT, reply_markup=dev_keyboard(), parse_mode="HTML")

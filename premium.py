from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from premium_kb import premium_kb

router = Router()

PREMIUM_TEXT = (
    "💎 <b>«PREMIUM» obunasi nima uchun kerak?</b>\n\n"
    "<blockquote>"
    "🚫 Kanallarga obuna bo'lish shart emas.\n"
    "🚫 Hech qanday reklamalarsiz.\n"
    "📈 Kerakli Animelar sifatli formatda.\n"
    "⭐️ Premium Animelarni ko'rish imkoniyati."
    "</blockquote>\n\n"
    "Sotib olish uchun pastdagi tugma orqali admin bilan to'g'ridan-to'g'ri bog'laning — "
    "narx va muddat bo'yicha shaxsan kelishasiz."
)


@router.message(Command("premium"))
async def premium_handler(message: Message):
    await message.answer(PREMIUM_TEXT, reply_markup=premium_kb(), parse_mode="HTML")

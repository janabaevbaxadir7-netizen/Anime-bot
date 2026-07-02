from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from database.requests import add_user, get_anime_by_code
from keyboards.main_menu import main_menu_kb
from handlers.anime import send_anime_card

router = Router()

WELCOME_TEXT = (
    "🤝 <b>Salom {name}</b>\n\n"
    "<blockquote>"
    "/rand - 🔀 Random Anime\n"
    "/top - 🏆 Top Anime\n"
    "/last - 🎬 Oxirgi yuklangan\n"
    "/help - ☎️ Qo'llab quvvatlash\n"
    "/premium - 💎 Premium\n"
    "/dev - 🧑‍💻 Dasturchi"
    "</blockquote>\n\n"
    "🕵️ <i>Anime nomi yoki kodini kiriting:</i>"
)


@router.message(CommandStart())
async def start_handler(message: Message):
    is_new = await add_user(
        tg_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username or "",
    )
    text = WELCOME_TEXT.format(name=message.from_user.full_name)
    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")


@router.callback_query(F.data == "main_menu")
async def main_menu_callback(call: CallbackQuery):
    text = WELCOME_TEXT.format(name=call.from_user.full_name)
    await call.message.edit_text(text, reply_markup=main_menu_kb(), parse_mode="HTML")
    await call.answer()


# Foydalanuvchi anime kodini (masalan "562") yozganda ishlaydi
@router.message(F.text.regexp(r"^\d+$"))
async def search_by_code(message: Message):
    code = int(message.text)
    anime = await get_anime_by_code(code)
    if not anime:
        await message.answer(f"❌ <b>{code}</b> kodi bo'yicha natija topilmadi.", parse_mode="HTML")
        return
    await message.answer(f"🔎 <b>{code}</b> qidiruvi bo'yicha natijalar: 1 ta", parse_mode="HTML")
    await send_anime_card(message, anime)


# Foydalanuvchi anime nomini yozganda ishlaydi
@router.message(F.text)
async def search_by_title(message: Message):
    from database.requests import search_anime_by_title
    from keyboards.anime_kb import anime_list_kb

    results = await search_anime_by_title(message.text)
    if not results:
        await message.answer("❌ Bunday nomdagi anime topilmadi.")
        return
    await message.answer(
        f"🔎 <b>{message.text}</b> qidiruvi bo'yicha natijalar: {len(results)} ta",
        reply_markup=anime_list_kb(results),
        parse_mode="HTML",
    )

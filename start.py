from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from crud import add_user, get_anime_by_code, get_saved_animes, is_premium, get_all_external_links
from main_menu import main_menu_kb
from anime import send_anime_card
from subscription import check_subscription, subscribe_kb, require_subscription_for_anime
from filters import is_admin_async

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

EXTLINK_TEXT = (
    "🔗 <b>Bizni kuzatib boring!</b>\n\n"
    "Botdan foydalanishdan oldin quyidagi manbalarimiz bilan tanishib chiqing "
    "(istasangiz kirib chiqing), so'ng pastdagi tugmani bosing:"
)


def external_links_kb(links) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=f"🔗 {l.title}", url=l.url)] for l in links]
    rows.append([InlineKeyboardButton(text="✅ Davom etish", callback_data="ext_continue")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _parse_anime_deep_link(args: str | None) -> int | None:
    """'anime_101' ko'rinishidagi deep-link argumentidan anime kodini ajratib oladi."""
    if not args or not args.startswith("anime_"):
        return None
    code_part = args.split("_", 1)[1]
    return int(code_part) if code_part.isdigit() else None


@router.message(CommandStart())
async def start_handler(message: Message, bot: Bot, state: FSMContext, command: CommandObject):
    is_new = await add_user(
        tg_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username or "",
    )

    # Kanal postidagi "🎬 Tomosha qilish" tugmasi bosilsa, /start ga
    # ?start=anime_101 ko'rinishida keladi — shu kodni saqlab qo'yamiz,
    # keyinroq (obuna talabidan o'tgach) shu animeni ko'rsatamiz.
    deep_link_code = _parse_anime_deep_link(command.args)
    if deep_link_code is not None:
        await state.update_data(pending_anime_code=deep_link_code)

    # MUHIM: majburiy obuna endi /start'da SO'RALMAYDI — foydalanuvchi darrov
    # menyuni ko'radi. Obuna talabi faqat aniq bir animeni ochmoqchi bo'lganda
    # (pastda, agar deep_link_code bo'lsa yoki qidiruv orqali) so'raladi.

    text = WELCOME_TEXT.format(name=message.from_user.full_name)

    # Faqat ENDI birinchi marta ro'yxatdan o'tgan foydalanuvchiga, tashqi
    # (Telegramdan tashqari) linklar bo'lsa — bir martalik ekran ko'rsatiladi.
    if is_new:
        links = await get_all_external_links()
        if links:
            await message.answer(EXTLINK_TEXT, reply_markup=external_links_kb(links), parse_mode="HTML")
            return

    await message.answer(text, reply_markup=await main_menu_kb(), parse_mode="HTML")

    if deep_link_code is not None:
        anime = await get_anime_by_code(deep_link_code)
        await state.update_data(pending_anime_code=None)
        if anime and await require_subscription_for_anime(message, bot, message.from_user.id, state, deep_link_code):
            await send_anime_card(message, anime)


@router.callback_query(F.data == "ext_continue")
async def ext_continue_cb(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Yangi foydalanuvchi 'Davom etish' tugmasini bosgach — bosh menyuga o'tadi."""
    try:
        await callback.message.delete()
    except Exception:
        pass
    text = WELCOME_TEXT.format(name=callback.from_user.full_name)
    await callback.message.answer(text, reply_markup=await main_menu_kb(), parse_mode="HTML")
    await callback.answer()

    data = await state.get_data()
    code = data.get("pending_anime_code")
    if code is not None:
        await state.update_data(pending_anime_code=None)
        anime = await get_anime_by_code(code)
        if anime and await require_subscription_for_anime(callback.message, bot, callback.from_user.id, state, code):
            await send_anime_card(callback, anime)


@router.callback_query(F.data == "check_sub")
async def check_sub_cb(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Foydalanuvchi biror animeni ochmoqchi bo'lib, obuna talab qilingandan keyin
    '✅ Tekshirish' tugmasini bosganda ishlaydi. Agar hali ham hammasiga obuna
    bo'lmagan bo'lsa — ro'yxat FAQAT qolgan (obuna bo'linmagan) kanallarga
    yangilanadi (masalan 5 tadan 3 tasiga obuna bo'lsa, endi faqat 2 tasi chiqadi)."""
    uid = callback.from_user.id
    if await is_admin_async(uid) or await is_premium(uid):
        ok, channels = True, []
    else:
        ok, channels = await check_subscription(bot, uid)

    if not ok:
        try:
            await callback.message.edit_reply_markup(reply_markup=subscribe_kb(channels))
        except Exception:
            pass
        await callback.answer("❌ Hali quyidagi kanal(lar)ga obuna bo'lmagansiz.", show_alert=True)
        return

    await callback.answer("✅ Obuna tasdiqlandi!")
    try:
        await callback.message.delete()
    except Exception:
        pass

    data = await state.get_data()
    code = data.get("pending_anime_code")
    if code is not None:
        await state.update_data(pending_anime_code=None)
        anime = await get_anime_by_code(code)
        if anime:
            await send_anime_card(callback, anime)


@router.callback_query(F.data == "main_menu")
async def main_menu_callback(call: CallbackQuery):
    text = WELCOME_TEXT.format(name=call.from_user.full_name)
    kb = await main_menu_kb()
    # Anime kartochkasi RASM bilan bo'lishi mumkin — bunday xabarni edit_text bilan
    # o'zgartirib bo'lmaydi (Telegram xato beradi). Shu sabab avval o'chirib,
    # keyin yangi matnli xabar yuboramiz — bu holatlarning barchasida ishlaydi.
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "saved_animes")
async def saved_animes_cb(call: CallbackQuery):
    from anime_kb import anime_list_kb
    animes = await get_saved_animes(call.from_user.id)
    if not animes:
        await call.answer("📭 Sizda hali saqlangan anime yo'q.", show_alert=True)
        return
    await call.message.answer(
        "⬇️ <b>Saqlangan Animelaringiz</b>",
        reply_markup=anime_list_kb(animes),
        parse_mode="HTML",
    )
    await call.answer()


# Foydalanuvchi anime kodini (masalan "562") yozganda ishlaydi
@router.message(F.text.regexp(r"^\d+$"))
async def search_by_code(message: Message, bot: Bot, state: FSMContext):
    code = int(message.text)
    anime = await get_anime_by_code(code)
    if not anime:
        await message.answer(f"❌ <b>{code}</b> kodi bo'yicha natija topilmadi.", parse_mode="HTML")
        return
    await message.answer(f"🔎 <b>{code}</b> qidiruvi bo'yicha natijalar: 1 ta", parse_mode="HTML")
    if await require_subscription_for_anime(message, bot, message.from_user.id, state, code):
        await send_anime_card(message, anime)


# Foydalanuvchi anime nomini yozganda ishlaydi
@router.message(F.text)
async def search_by_title(message: Message):
    from crud import search_anime_by_title
    from anime_kb import anime_list_kb

    results = await search_anime_by_title(message.text)
    if not results:
        await message.answer("❌ Bunday nomdagi anime topilmadi.")
        return
    await message.answer(
        f"🔎 <b>{message.text}</b> qidiruvi bo'yicha natijalar: {len(results)} ta",
        reply_markup=anime_list_kb(results),
        parse_mode="HTML",
    )

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from crud import add_user, get_anime_by_code, get_saved_animes, is_premium
import crud
from main_menu import main_menu_kb
from anime import send_anime_card
from subscription import check_subscription
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
    "/earn - 💰 Pul ishlash\n"
    "/dev - 🧑‍💻 Dasturchi"
    "</blockquote>\n\n"
    "🕵️ <i>Anime nomi yoki kodini kiriting:</i>"
)


def subscribe_kb(channels):
    rows = [[InlineKeyboardButton(text=f"➕ {ch.title or 'Kanal'}", url=ch.url)] for ch in channels if ch.url]
    rows.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _parse_anime_deep_link(args: str | None) -> int | None:
    """'anime_101' ko'rinishidagi deep-link argumentidan anime kodini ajratib oladi."""
    if not args or not args.startswith("anime_"):
        return None
    code_part = args.split("_", 1)[1]
    return int(code_part) if code_part.isdigit() else None


def _parse_ref_deep_link(args: str | None) -> int | None:
    """'ref_123456789' ko'rinishidagi deep-link argumentidan referrer tg_id sini ajratib oladi."""
    if not args or not args.startswith("ref_"):
        return None
    id_part = args.split("_", 1)[1]
    return int(id_part) if id_part.isdigit() else None


async def _try_notify_referral_credit(bot: Bot, referred_id: int):
    """EarnChannel'larga obuna tekshiriladi, agar shart bajarilgan bo'lsa
    referrerga pul qo'shiladi va unga xabar yuboriladi."""
    amount, referrer_id = await crud.try_credit_referral(bot, referred_id)
    if amount > 0 and referrer_id:
        try:
            await bot.send_message(
                referrer_id,
                f"🎉 Tabriklaymiz! Sizning taklifingiz orqali yangi foydalanuvchi qo'shildi.\n"
                f"💰 Balansingizga <b>+{amount} so'm</b> tushdi!",
                parse_mode="HTML"
            )
        except Exception:
            pass


@router.message(CommandStart())
async def start_handler(message: Message, bot: Bot, state: FSMContext, command: CommandObject):
    is_new = await add_user(
        tg_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username or "",
    )

    # Kanal postidagi "🎬 Tomosha qilish" tugmasi bosilsa, /start ga
    # ?start=anime_101 ko'rinishida keladi — shu kodni saqlab qo'yamiz,
    # obuna tekshiruvidan o'tgach avtomatik shu animeni ko'rsatamiz.
    deep_link_code = _parse_anime_deep_link(command.args)
    if deep_link_code is not None:
        await state.update_data(pending_anime_code=deep_link_code)

    # Referal orqali kirgan bo'lsa (?start=ref_<tg_id>) — faqat YANGI foydalanuvchi uchun qayd etiladi.
    ref_id = _parse_ref_deep_link(command.args)
    if is_new and ref_id is not None:
        await crud.set_referred_by(message.from_user.id, ref_id)

    # Har /start bosilganda EarnChannel'larga obunani tekshirib, kerak bo'lsa referrerga pul qo'shamiz
    await _try_notify_referral_credit(bot, message.from_user.id)

    # Adminlar va Premium foydalanuvchilar uchun majburiy obuna talab qilinmaydi
    if not await is_admin_async(message.from_user.id) and not await is_premium(message.from_user.id):
        ok, channels = await check_subscription(bot, message.from_user.id)
        if not ok:
            await message.answer(
                "⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling!",
                reply_markup=subscribe_kb(channels)
            )
            return

    text = WELCOME_TEXT.format(name=message.from_user.full_name)
    await message.answer(text, reply_markup=await main_menu_kb(), parse_mode="HTML")

    if deep_link_code is not None:
        anime = await get_anime_by_code(deep_link_code)
        await state.update_data(pending_anime_code=None)
        if anime:
            await send_anime_card(message, anime)


@router.callback_query(F.data == "check_sub")
async def check_sub_cb(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await _try_notify_referral_credit(bot, callback.from_user.id)
    ok, channels = (True, []) if await is_premium(callback.from_user.id) else await check_subscription(bot, callback.from_user.id)
    if not ok:
        await callback.answer("❌ Hali barcha kanallarga obuna bo'lmadingiz.", show_alert=True)
        return
    await callback.message.delete()
    text = WELCOME_TEXT.format(name=callback.from_user.full_name)
    await callback.message.answer(text, reply_markup=await main_menu_kb(), parse_mode="HTML")
    await callback.answer()

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

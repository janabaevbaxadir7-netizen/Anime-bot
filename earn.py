from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

import config, crud
from states import EarnStates

router = Router()

MIN_WITHDRAW = 10_000  # minimal yechish summasi, so'm


def earn_menu_kb() -> "InlineKeyboardMarkup":
    kb = InlineKeyboardBuilder()
    kb.button(text="💳 Pul yechish", callback_data="earn_withdraw")
    kb.button(text="🔄 Yangilash", callback_data="earn_refresh")
    kb.button(text="🏠 Bosh Menyu", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()


async def _earn_text(bot: Bot, user_id: int) -> str:
    bot_username = (await bot.get_me()).username
    link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    stats = await crud.get_referral_stats(user_id)
    channels = await crud.get_all_earn_channels()
    if channels:
        ch_lines = "\n".join(f"• {ch.title or ch.chat_id} — <b>{ch.reward} so'm</b>" for ch in channels)
        reward_block = (
            "\n\n📋 <b>Zayavka kanallari</b> — do'stingiz botga kirib, shu kanal(lar)ga "
            f"obuna bo'lsa, sizga pul tushadi:\n{ch_lines}"
        )
    else:
        reward_block = "\n\n⚠️ Hozircha faol zayavka kanallari yo'q, keyinroq qayta tekshiring."
    return (
        "💰 <b>Pul ishlash</b>\n\n"
        f"🔗 Sizning referal havolangiz:\n<code>{link}</code>\n\n"
        f"👥 Taklif qilinganlar: <b>{stats['total']}</b> ta\n"
        f"✅ Tasdiqlanganlar: <b>{stats['credited']}</b> ta\n"
        f"💵 Balansingiz: <b>{stats['balance']} so'm</b>"
        f"{reward_block}"
    )


@router.message(Command("earn"))
@router.message(F.text == "💰 Pul ishlash")
async def earn_menu(message: Message, bot: Bot, state: FSMContext):
    await state.clear()
    await message.answer(await _earn_text(bot, message.from_user.id), reply_markup=earn_menu_kb(), parse_mode="HTML")


@router.callback_query(F.data == "earn_menu")
async def earn_menu_cb(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await state.clear()
    text = await _earn_text(bot, callback.from_user.id)
    try:
        await callback.message.edit_text(text, reply_markup=earn_menu_kb(), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=earn_menu_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "earn_refresh")
async def earn_refresh_cb(callback: CallbackQuery, bot: Bot):
    try:
        await callback.message.edit_text(
            await _earn_text(bot, callback.from_user.id), reply_markup=earn_menu_kb(), parse_mode="HTML"
        )
        await callback.answer("🔄 Yangilandi")
    except Exception:
        await callback.answer()


@router.callback_query(F.data == "earn_withdraw")
async def earn_withdraw_start(callback: CallbackQuery, state: FSMContext):
    stats = await crud.get_referral_stats(callback.from_user.id)
    if stats["balance"] < MIN_WITHDRAW:
        await callback.answer(
            f"⚠️ Yechish uchun kamida {MIN_WITHDRAW} so'm balansda bo'lishi kerak.\n"
            f"Hozirgi balansingiz: {stats['balance']} so'm.",
            show_alert=True
        )
        return
    await callback.message.answer(
        f"💳 Balansingiz: <b>{stats['balance']} so'm</b>\n\nQancha summa yechmoqchisiz? (raqam bilan yuboring):",
        parse_mode="HTML"
    )
    await state.set_state(EarnStates.waiting_withdraw_amount)
    await callback.answer()


@router.message(EarnStates.waiting_withdraw_amount)
async def earn_withdraw_amount(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam yuboring."); return
    amount = int(message.text.strip())
    stats = await crud.get_referral_stats(message.from_user.id)
    if amount < MIN_WITHDRAW:
        await message.answer(f"❌ Minimal summa {MIN_WITHDRAW} so'm."); return
    if amount > stats["balance"]:
        await message.answer(f"❌ Balansingizda yetarli mablag' yo'q. Balans: {stats['balance']} so'm."); return
    await state.update_data(withdraw_amount=amount)
    await message.answer("💳 Click yoki Payme karta raqamingizni yuboring (masalan: 8600 1234 5678 9012):")
    await state.set_state(EarnStates.waiting_withdraw_card)


@router.message(EarnStates.waiting_withdraw_card)
async def earn_withdraw_card(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    amount = data.get("withdraw_amount")
    card = message.text.strip()
    wr = await crud.create_withdraw_request(message.from_user.id, amount, card)
    await state.clear()
    if not wr:
        await message.answer("❌ Xatolik yuz berdi (balans yetarli emas). Qaytadan urinib ko'ring.")
        return
    await message.answer(
        f"✅ So'rovingiz qabul qilindi!\n💵 Summa: {amount} so'm\n💳 Karta: <code>{card}</code>\n\n"
        f"Admin tez orada ko'rib chiqib, to'lovni amalga oshiradi.",
        parse_mode="HTML"
    )
    admin_ids = set(config.ADMIN_IDS)
    for a in await crud.list_admins():
        if "earn" in (a.permissions or ""):
            admin_ids.add(a.id)
    for aid in admin_ids:
        try:
            await bot.send_message(
                aid,
                f"💳 <b>Yangi pul yechish so'rovi!</b>\n\n"
                f"👤 {message.from_user.full_name} (<code>{message.from_user.id}</code>)\n"
                f"💵 Summa: {amount} so'm\n"
                f"💳 Karta: <code>{card}</code>\n"
                f"🆔 So'rov ID: {wr.id}\n\n"
                f"Ko'rib chiqish uchun: /admin → 💰 Pul ishlash → 📋 Yechish so'rovlari",
                parse_mode="HTML"
            )
        except Exception:
            pass

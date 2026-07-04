from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    # Anime
    waiting_new_title = State()
    waiting_new_description = State()
    waiting_episodes = State()
    waiting_code_for_ep = State()
    waiting_episodes_existing = State()
    waiting_code_for_edit = State()
    waiting_edit_title = State()
    waiting_edit_description = State()
    waiting_code_for_delete = State()
    waiting_code_for_full_delete = State()

    # Kanallar
    waiting_channel_id = State()
    waiting_channel_title = State()
    waiting_channel_url = State()

    # Xabarnoma
    waiting_broadcast = State()

    # Foydalanuvchi
    waiting_user_query = State()
    waiting_premium_days = State()

    # Adminlar
    waiting_add_admin_id = State()
    waiting_remove_admin_id = State()

    # Post tayyorlash
    waiting_post_code = State()
    waiting_post_channel = State()          # eski (endi ishlatilmaydi, orqaga moslik uchun qoldirildi)
    waiting_post_new_channel = State()      # yangi kanal ID/username kiritilayotganda
    waiting_post_photo = State()
    waiting_post_caption = State()

    # Anime premium sozlash
    waiting_premium_anime_days = State()

    # Pul ishlash — Zayavka kanallari (admin)
    waiting_earn_channel_id = State()
    waiting_earn_channel_title = State()
    waiting_earn_channel_url = State()
    waiting_earn_channel_reward = State()


class EarnStates(StatesGroup):
    # Pul ishlash — foydalanuvchi tomoni
    waiting_withdraw_amount = State()
    waiting_withdraw_card = State()


class SupportStates(StatesGroup):
    waiting_feedback_text = State()

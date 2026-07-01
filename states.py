from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    waiting_gender = State()
    waiting_code = State()
    waiting_feedback = State()


class AdminStates(StatesGroup):
    waiting_new_title = State()
    waiting_episodes = State()  # yangi anime uchun qism forward qilish
    waiting_anime_code_for_ep = State()
    waiting_episodes_existing = State()  # mavjud animega qism qo'shish
    waiting_channel_id = State()
    waiting_channel_title = State()
    waiting_channel_url = State()
    waiting_broadcast_text = State()
    waiting_delete_code = State()

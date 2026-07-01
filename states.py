from aiogram.fsm.state import State, StatesGroup

class UserStates(StatesGroup):
    waiting_gender   = State()
    waiting_code     = State()
    waiting_feedback = State()

class AdminStates(StatesGroup):
    waiting_new_title          = State()
    waiting_episodes           = State()
    waiting_anime_code_for_ep  = State()
    waiting_episodes_existing  = State()
    waiting_channel_id         = State()
    waiting_channel_title      = State()
    waiting_channel_url        = State()
    waiting_broadcast_text     = State()
    waiting_rename             = State()
    waiting_description        = State()
    waiting_cover              = State()
    waiting_add_admin          = State()
    waiting_remove_admin       = State()


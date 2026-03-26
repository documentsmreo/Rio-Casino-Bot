from aiogram.fsm.state import State, StatesGroup

from aiogram.fsm.state import State, StatesGroup

class BroadcastState(StatesGroup):
    menu = State()
    text = State()
    photo = State()
    button_text = State()
    button_url = State()

class SupportState(StatesGroup):
    question = State()

class DepositState(StatesGroup):
    amount = State()
    withdraw_amount = State()

class AdminState(StatesGroup):
    menu = State()
    mailing = State()
    promo_amount = State()
    promo_count = State()
    promo_time = State()
    promo_delete = State()
    edit_coefficient = State()
    pvp_cancel_id = State()
    moderator_id = State()
    treasury_deposit = State()

class GameState(StatesGroup):
    bet_amount = State()
    mode = State()
    playing = State()

class PvPState(StatesGroup):
    bet_amount = State()
    making_move = State()

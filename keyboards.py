from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import CHANNEL_LINK

def get_subscription_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подписаться на канал", url=CHANNEL_LINK)],
        [InlineKeyboardButton(text="Я подписался", callback_data="check_subscription")]
    ])
    return keyboard

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Профиль"), KeyboardButton(text="Игры")],
        [KeyboardButton(text="Поддержка")]
    ], resize_keyboard=True)
    return keyboard

def get_admin_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📨 Рассылка", callback_data="admin_mailing")],
        [InlineKeyboardButton(text="🎫 Промокоды", callback_data="admin_promos")],
        [InlineKeyboardButton(text="⚙️ Настройки игр", callback_data="admin_games")],
        [InlineKeyboardButton(text="👮 Модераторы", callback_data="admin_moderators")],
        [InlineKeyboardButton(text="💰 Казна", callback_data="admin_treasury")]
    ])

def get_admin_mailing_keyboard(data):
    has_text = "✅" if data.get('text') else "❌"
    has_photo = "✅" if data.get('photo') else "❌"
    has_button = "✅" if data.get('button_text') and data.get('button_url') else "❌"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Текст {has_text}", callback_data="admin_text"),
         InlineKeyboardButton(text=f"Фото {has_photo}", callback_data="admin_photo")],
        [InlineKeyboardButton(text=f"Кнопка {has_button}", callback_data="admin_button")],
        [InlineKeyboardButton(text="Начать рассылку", callback_data="admin_send")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back_main")]
    ])
    return keyboard

def get_admin_promos_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Список", callback_data="promo_list")],
        [InlineKeyboardButton(text="Добавить", callback_data="promo_add")],
        [InlineKeyboardButton(text="Удалить", callback_data="promo_delete")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back_main")]
    ])

def get_admin_promo_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Кол-во активаций", callback_data="promo_type_activations")],
        [InlineKeyboardButton(text="Время действия", callback_data="promo_type_time")]
    ])

def get_profile_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Пополнить", callback_data="deposit"),
         InlineKeyboardButton(text="💸 Вывод", callback_data="withdraw")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="profile_stats")],
        [InlineKeyboardButton(text="🎫 Промокод", callback_data="profile_promo")],
        [InlineKeyboardButton(text="👥 Реферальная система", callback_data="profile_referral")]
    ])

def get_withdraw_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Вывести", callback_data="withdraw_start")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="profile_back")]
    ])

def get_profile_back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="profile_back")]
    ])

def get_deposit_methods_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💠 CryptoBot", callback_data="dep_cryptobot")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="profile_back")]
    ])

def get_back_keyboard(callback_data="deposit_back"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data=callback_data)]
    ])

def get_currencies_keyboard():
    currencies = ["USDT", "TON", "LTC", "ETH", "BTC"]
    buttons = []
    for cur in currencies:
        buttons.append([InlineKeyboardButton(text=cur, callback_data=f"pay_{cur}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="dep_cryptobot")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_payment_keyboard(pay_url, invoice_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Оплатить", url=pay_url)],
        [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data=f"check_pay_{invoice_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="deposit_amount_back")]
    ])

def get_games_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Игры с ботом", callback_data="games_bot")],
        [InlineKeyboardButton(text="👥 Игры с игроками", callback_data="games_players")],
        [InlineKeyboardButton(text="💬 Чат", url="https://t.me/+tyAZm1FrswYyYTdi")]
    ])

def get_bot_games_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="21 Очко", callback_data="game_21"), InlineKeyboardButton(text="✊✌✋ ЦУЕФА", callback_data="game_rps")],
        [InlineKeyboardButton(text="⚽ Футбол", callback_data="game_football"), InlineKeyboardButton(text="🎯 Дартс", callback_data="game_darts")],
        [InlineKeyboardButton(text="🎳 Боулинг", callback_data="game_bowling"), InlineKeyboardButton(text="🏀 Баскетбол", callback_data="game_basketball")],
        [InlineKeyboardButton(text="🎲 Кубик", callback_data="game_dice")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="games_main")]
    ])

def get_pvp_move_keyboard(game_type="dice"):
    emoji_map = {
        "dice": "🎲", "football": "⚽", "basketball": "🏀", 
        "darts": "🎯", "bowling": "🎳"
    }
    emoji = emoji_map.get(game_type, "🎲")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{emoji} Сделать ход", callback_data="pvp_make_move")]
    ])

def get_pvp_join_move_keyboard(game_id, game_type="dice"):
    emoji_map = {
        "dice": "🎲", "football": "⚽", "basketball": "🏀", 
        "darts": "🎯", "bowling": "🎳"
    }
    emoji = emoji_map.get(game_type, "🎲")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{emoji} Сделать ход", callback_data=f"pvp_join_move_{game_id}")]
    ])

def get_games_players_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать игру", callback_data="pvp_create")],
        [InlineKeyboardButton(text="📋 Список игр", callback_data="pvp_list")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="games_main")]
    ])

def get_pvp_create_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Кубик", callback_data="pvp_type_dice"), InlineKeyboardButton(text="⚽ Футбол", callback_data="pvp_type_football")],
        [InlineKeyboardButton(text="🏀 Баскетбол", callback_data="pvp_type_basketball"), InlineKeyboardButton(text="🎯 Дартс", callback_data="pvp_type_darts")],
        [InlineKeyboardButton(text="🎳 Боулинг", callback_data="pvp_type_bowling")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="games_players")]
    ])

def get_pvp_games_list_keyboard(games):
    kb = []
    emoji_map = {
        "dice": "🎲", "football": "⚽", "basketball": "🏀", 
        "darts": "🎯", "bowling": "🎳"
    }
    
    for game in games:
        game_id, game_type, _, creator_name, bet, _ = game
        emoji = emoji_map.get(game_type, "🎮")
        text = f"{emoji} | {bet} RUB | {creator_name}"
        kb.append([InlineKeyboardButton(text=text, callback_data=f"pvp_join_{game_id}")])
        
    kb.append([InlineKeyboardButton(text="🔄 Обновить", callback_data="pvp_list")])
    kb.append([InlineKeyboardButton(text="◀️ Назад", callback_data="games_players")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_pvp_bet_cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="pvp_cancel_create")]
    ])

def get_rps_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✊ Камень", callback_data="rps_rock"), InlineKeyboardButton(text="✂️ Ножницы", callback_data="rps_scissors"), InlineKeyboardButton(text="✋ Бумага", callback_data="rps_paper")],
        [InlineKeyboardButton(text="◀️ Выход", callback_data="game_exit")]
    ])

def get_21_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Взять карту", callback_data="21_hit"), InlineKeyboardButton(text="🛑 Хватит", callback_data="21_stand")],
        [InlineKeyboardButton(text="◀️ Выход", callback_data="game_exit")]
    ])

def get_admin_games_keyboard(coefficients):
    kb = []
    limit = 2
    row = []
    
    games_map = [
        ("game_21", "21 Очко"),
        ("game_rps", "ЦУЕФА"),
        ("game_darts", "Дартс"),
        ("game_bowling", "Боулинг"),
        ("game_football_points", "Футбол (Очки)"),
        ("game_football_specific", "Футбол (Исход)"),
        ("game_basketball_points", "Баскет (Очки)"),
        ("game_basketball_specific", "Баскет (Исход)"),
        ("game_dice_points", "Кубик (Очки)"),
        ("game_dice_overunder", "Кубик (Б/М)")
    ]
    
    for game_id, name in games_map:
        coeff = coefficients.get(game_id, 2.0)
        row.append(InlineKeyboardButton(text=f"{name} (x{coeff})", callback_data=f"admin_coef_{game_id}"))
        if len(row) == limit:
            kb.append(row)
            row = []
    
    if row:
        kb.append(row)
        
    kb.append([InlineKeyboardButton(text="🗑 Отменить PvP игру", callback_data="admin_pvp_cancel_menu")])
    kb.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_game_menu_keyboard(game_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Играть", callback_data=f"play_{game_id}")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data=f"stats_{game_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="games_bot")]
    ])

def get_game_stats_back_keyboard(game_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"game_{game_id}")]
    ])

def get_game_bet_back_keyboard(game_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data=game_id)]
    ])

def get_game_mode_keyboard(game_id):
    if game_id in ["game_football", "game_basketball"]:
         return InlineKeyboardMarkup(inline_keyboard=[
             [InlineKeyboardButton(text="🎯 По очкам", callback_data="mode_points")],
             [InlineKeyboardButton(text="🏹 Выборочно", callback_data="mode_specific")]
         ])
    elif game_id == "game_dice":
         return InlineKeyboardMarkup(inline_keyboard=[
             [InlineKeyboardButton(text="🎲 По очкам", callback_data="mode_points")],
             [InlineKeyboardButton(text="↕️ Больше/Меньше", callback_data="mode_overunder")]
         ])
    return None

def get_game_choice_keyboard(game_id):
    if game_id == "game_football":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚽ Забью", callback_data="choice_hit"), InlineKeyboardButton(text="❌ Промах", callback_data="choice_miss")]
        ])
    elif game_id == "game_basketball":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏀 Забью", callback_data="choice_hit"), InlineKeyboardButton(text="❌ Промах", callback_data="choice_miss")]
        ])
    elif game_id == "game_dice":
         return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📉 1-3", callback_data="choice_under"), InlineKeyboardButton(text="📈 4-6", callback_data="choice_over")]
         ])
    return None

def get_chat_game_keyboard(game_id, game_type="dice"):
    emoji_map = {
        "dice": "🎲", "football": "⚽", "basketball": "🏀", 
        "darts": "🎯", "bowling": "🎳"
    }
    emoji = emoji_map.get(game_type, "🎲")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{emoji} Сделать ход", callback_data=f"chat_game_move_{game_id}")]
    ])

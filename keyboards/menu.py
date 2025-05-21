from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu() -> InlineKeyboardMarkup:
    """Get main menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
            InlineKeyboardButton(text="📊 Рейтинг", callback_data="rating")
        ],
        [
            InlineKeyboardButton(text="✅ Чек-ин", callback_data="check_in"),
            InlineKeyboardButton(text="📝 Задания", callback_data="tasks")
        ],
        [
            InlineKeyboardButton(text="🎮 Игры", callback_data="games"),
            InlineKeyboardButton(text="🎁 Награды", callback_data="rewards")
        ],
        [
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_profile_menu() -> InlineKeyboardMarkup:
    """Get profile menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(text="🏆 Достижения", callback_data="achievements"),
            InlineKeyboardButton(text="📈 Статистика", callback_data="stats")
        ],
        [
            InlineKeyboardButton(text="👥 Рефералы", callback_data="referrals"),
            InlineKeyboardButton(text="📅 История", callback_data="history")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 
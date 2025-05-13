from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config.constants import MAIN_MENU, ADMIN_MENU

def get_main_keyboard():
    """Get main menu keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ CHECK-IN"), KeyboardButton(text="📋 Задание дня")],
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="🏆 Топ")],
            [KeyboardButton(text="🤝 Реферал"), KeyboardButton(text="💎 Достижения")],
            [KeyboardButton(text="💸 Донат"), KeyboardButton(text="ℹ️ Команды")]
        ],
        resize_keyboard=True
    )

def get_group_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ CHECK-IN")],
            [KeyboardButton(text="🏆 Топ"), KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="💸 Задонать себе на будущее!")]
        ],
        resize_keyboard=True
    )

def get_admin_keyboard():
    """Get admin menu keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 Рассылка"), KeyboardButton(text="✏️ Создать задание")],
            [KeyboardButton(text="👥 Пользователи"), KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="🔧 Обслуживание")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )

def get_subscription_keyboard(subscriptions):
    """Get subscription check keyboard"""
    keyboard = []
    for sub_id, url, type in subscriptions:
        keyboard.append([InlineKeyboardButton(
            text=f"Подписаться на {type}",
            url=url
        )])
    keyboard.append([InlineKeyboardButton(
        text="✅ Проверить подписки",
        callback_data="check_subscriptions"
    )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_referral_keyboard(bot_username: str, user_id: int):
    """Get referral link keyboard"""
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📢 Поделиться ссылкой",
            url=f"https://t.me/share/url?url={ref_link}&text=Присоединяйся к SisuDatuBot!"
        )]
    ])

def get_donate_keyboard():
    """Get donate keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="💎 Купить Sisu",
            url="https://t.me/tontrade?start=HeeuA1fNBh"
        )]
    ])

def get_task_keyboard():
    """Get daily task keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Выполнить задание",
            callback_data="complete_task"
        )]
    ])

def get_profile_keyboard():
    """Get profile keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🏆 Топ участников",
            callback_data="show_top"
        )],
        [InlineKeyboardButton(
            text="💎 Достижения",
            callback_data="show_achievements"
        )]
    ]) 
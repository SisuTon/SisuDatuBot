import os
from dotenv import load_dotenv

load_dotenv()

# Bot token
BOT_TOKEN = "7803467562:AAEBRUONmWrYumXycItBKWUqXhmnVBpqe0Y"

# Super admins
SUPER_ADMINS = {
    446318189,  # @bakeevsergey
    5857816562  # @SISU_TON
}

# Required subscriptions
REQUIRED_SUBSCRIPTIONS = {
    "channel": "https://t.me/SisuDatuTon",  # ссылка на канал
    "chat": "https://t.me/+3uHf68NemIQ0ZjVi",  # ссылка на чат
    "twitter": "https://x.com/SisuTon"
}

# Points configuration
POINTS_CONFIG = {
    "text": {
        "min_words": 10,      # Минимум 10 слов
        "points": 1.0,        # Базовый балл
        "bonus_words": 50,    # Количество слов для бонуса
        "bonus_points": 2.0   # Бонусные баллы за длинное сообщение
    },
    "photo": {
        "points": 0.5,        # Базовый балл за фото
        "with_caption": 0.3   # Дополнительные баллы за подпись
    },
    "video": {
        "points": 1.0,        # Базовый балл за видео
        "with_caption": 0.5   # Дополнительные баллы за описание
    },
    "check_in": {
        "points": 10,         # Базовый балл за чек-ин
        "streak_bonus": {     # Бонусы за серию дней
            7: 5,             # +5 баллов за 7 дней
            30: 20,           # +20 баллов за 30 дней
            100: 50           # +50 баллов за 100 дней
        }
    },
    "referral": {
        "points": 10,         # Баллы за реферала
        "bonus_per_referral": 5  # Дополнительные баллы за каждого следующего реферала
    },
    "time_bonus": {           # Бонусы за время активности
        "morning": {          # Утренний бонус (6:00 - 9:00)
            "multiplier": 1.5
        },
        "evening": {          # Вечерний бонус (20:00 - 23:00)
            "multiplier": 1.3
        }
    }
}

# Database
DATABASE_PATH = "sisudatu.db"

# Ranks configuration
RANKS = [
    {"name": "Новичок", "emoji": "🌱", "min_points": 0},
    {"name": "Активный", "emoji": "🌿", "min_points": 100},
    {"name": "Опытный", "emoji": "🌳", "min_points": 500},
    {"name": "Мастер", "emoji": "🎯", "min_points": 1000},
    {"name": "Легенда", "emoji": "👑", "min_points": 5000}
] 
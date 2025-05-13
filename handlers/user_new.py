from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from config.settings import POINTS_CONFIG, SUPER_ADMINS, REQUIRED_SUBSCRIPTIONS
from config.constants import WELCOME_MESSAGE, PHOTO_PHRASES, VIDEO_PHRASES, TEXT_PHRASES
from database.models import (
    add_user, get_user, add_points, get_top_users,
    add_achievement, get_user_achievements, get_current_task,
    get_subscriptions, update_check_in
)
from keyboards.keyboards import (
    get_main_keyboard, get_subscription_keyboard,
    get_referral_keyboard, get_donate_keyboard,
    get_task_keyboard, get_profile_keyboard,
    get_group_keyboard, get_admin_keyboard
)
import random
from datetime import datetime, timedelta
import re
from collections import defaultdict

router = Router()

# Словари для отслеживания активности пользователей
user_last_message = defaultdict(datetime)  # Время последнего сообщения
user_message_count = defaultdict(int)      # Количество сообщений за период
user_message_history = defaultdict(list)   # История последних сообщений
SPAM_THRESHOLD = 5  # Максимальное количество сообщений за период
SPAM_PERIOD = 60    # Период в секундах
MESSAGE_HISTORY_SIZE = 3  # Количество последних сообщений для проверки повторов

@router.message(F.text == "✅ CHECK-IN")
async def check_in(message: Message):
    """Handle daily check-in"""
    # Запрет начисления чек-ина в личке
    if message.chat.type == "private":
        await message.answer("Чек-ин доступен только в группе!")
        return
    
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала напишите /start")
        return
    
    points, streak, last_check_in, *_ = user
    now = datetime.now()
    
    # Проверка на 24-часовой интервал
    if last_check_in:
        last_check = datetime.fromisoformat(last_check_in)
        time_diff = now - last_check
        if time_diff.total_seconds() < 24 * 3600:  # 24 часа в секундах
            next_check = last_check + timedelta(hours=24)
            await message.answer(
                f"⏳ Вы уже сделали чек-ин!\nСледующий чек-ин будет доступен после {next_check.strftime('%d.%m %H:%M')}")
            return
    
    # Add points and update streak
    points_to_add = POINTS_CONFIG["check_in"]["points"]
    await add_points(message.from_user.id, points_to_add)
    new_streak = streak + 1 if streak else 1
    
    # Обновляем время последнего чек-ина и серию
    await update_check_in(message.from_user.id, new_streak)
    
    await message.answer(
        f"✅ Чек-ин выполнен!\n+{points_to_add} баллов\n🔥 Серия: {new_streak} дней"
    ) 
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from config.settings import POINTS_CONFIG, SUPER_ADMINS, REQUIRED_SUBSCRIPTIONS
from config.constants import WELCOME_MESSAGE, PHOTO_PHRASES, VIDEO_PHRASES, TEXT_PHRASES, ACHIEVEMENTS
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
from aiogram.utils.chat_action import ChatActionSender
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

# Словари для отслеживания активности пользователей
user_last_message = defaultdict(datetime)  # Время последнего сообщения
user_message_count = defaultdict(int)      # Количество сообщений за период
user_message_history = defaultdict(list)   # История последних сообщений
SPAM_THRESHOLD = 5  # Максимальное количество сообщений за период
SPAM_PERIOD = 60    # Период в секундах
MESSAGE_HISTORY_SIZE = 3  # Количество последних сообщений для проверки повторов

# Словарь для хранения id последнего сообщения с заданием дня для каждого пользователя
last_task_message = {}

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

@router.message(Command("start"))
async def cmd_start(message: Message):
    if message.chat.type == "private":
        await message.answer(
            "Добро пожаловать! Вот ваше меню:\n\n"
            "✅ CHECK-IN — ежедневная отметка\n"
            "📋 Задание дня — посмотреть задание\n"
            "👤 Профиль — ваш профиль\n"
            "🏆 Топ — топ участников\n"
            "🤝 Реферал — пригласить друзей\n"
            "💎 Достижения — ваши достижения\n"
            "💸 Донат — поддержать проект",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer("Бот активен! Используйте команды в личке для управления.")

@router.message(Command("menu"))
async def cmd_menu(message: Message):
    if message.chat.type == "private":
        await message.answer(
            "Меню:\n\n"
            "✅ CHECK-IN — ежедневная отметка\n"
            "📋 Задание дня — посмотреть задание\n"
            "👤 Профиль — ваш профиль\n"
            "🏆 Топ — топ участников\n"
            "🤝 Реферал — пригласить друзей\n"
            "💎 Достижения — ваши достижения\n"
            "💸 Донат — поддержать проект",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer("Меню доступно только в личном чате с ботом.")

@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала напишите /start")
        return
    points, streak, last_check_in, last_task_date, tasks_today, is_banned = user
    text = (
        f"<b>👤 Ваш профиль</b>\n"
        f"Баллы: <b>{points:.1f}</b>\n"
        f"Серия дней: <b>{streak}</b>\n"
        f"Выполнено заданий сегодня: <b>{tasks_today}</b>\n"
    )
    await message.answer(text)

@router.message(F.text == "🏆 Топ")
async def show_top(message: Message):
    top_users = await get_top_users(10)
    if not top_users:
        await message.answer("Топ пуст.")
        return
    medals = ["🥇", "🥈", "🥉"]
    text = "🏆 <b>Топ участников:</b>\n\n"
    for i, (username, points) in enumerate(top_users, 1):
        name = f"@{username}" if username else "Без ника"
        medal = medals[i-1] if i <= 3 else f"{i}."
        text += f"{medal} {name} — <b>{points:.1f}</b> баллов\n"
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "💎 Достижения")
async def show_achievements(message: Message):
    achievements = await get_user_achievements(message.from_user.id)
    if not achievements:
        await message.answer("У вас пока нет достижений.")
        return
    ach_map = {a['id']: a for a in ACHIEVEMENTS}
    text = "<b>💎 Ваши достижения:</b>\n\n"
    for ach_id in achievements:
        ach = ach_map.get(ach_id)
        if ach:
            text += f"{ach['emoji']} <b>{ach['name']}</b> — {ach['description']}\n"
    await message.answer(text)

@router.message(F.text == "🤝 Реферал")
async def show_referral(message: Message):
    bot_username = (await message.bot.me()).username
    ref_link = f"https://t.me/{bot_username}?start={message.from_user.id}"
    text = (
        f"<b>🤝 Ваша реферальная ссылка:</b>\n"
        f"{ref_link}\n\n"
        f"Пригласите друзей и получайте бонусы!"
    )
    await message.answer(text)

async def show_task(message: Message):
    task = await get_current_task()
    if not task:
        await message.answer("Сису готовит новое задание дня! Следите за обновлениями.")
        return
    # Удаляем предыдущее сообщение с заданием дня, если оно есть
    prev_msg_id = last_task_message.get(message.from_user.id)
    if prev_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, prev_msg_id)
        except Exception:
            pass
    sent = await message.answer(
        f"<b>📋 Задание дня:</b>\n\n{task}",
        reply_markup=get_task_keyboard()
    )
    last_task_message[message.from_user.id] = sent.message_id

@router.message(F.text == "📋 Задание дня")
async def show_task_button(message: Message):
    await show_task(message)

@router.callback_query(F.data == "complete_task")
async def complete_task_callback(callback: CallbackQuery):
    await callback.answer("Сису скоро добавит новое задание! Ожидайте.", show_alert=True)

@router.message(F.text == "💸 Донат")
async def show_donate(message: Message):
    await message.answer(
        "<b>💸 Задонать себе на будущее!</b>\n\n"
        "Купи Sisu — токен будущего. Это твой вклад в развитие проекта и возможность получить преимущества в будущем!\n\n"
        "<a href='https://t.me/tontrade?start=HeeuA1fNBh'>Купить Sisu</a>",
        parse_mode="HTML",
        disable_web_page_preview=True
    )

@router.message(F.text == "ℹ️ Команды")
async def show_commands(message: Message):
    await message.answer(
        "Доступные команды:\n"
        "/start — главное меню\n"
        "/menu — главное меню\n"
        "/profile — ваш профиль\n"
        "/top — топ участников\n"
        "/task — задание дня\n"
        "/referral — ваша реферальная ссылка\n"
        "/achievements — ваши достижения\n"
        "/donate — поддержать проект"
    )

@router.message(Command("task"))
async def cmd_task(message: Message):
    await show_task(message)

@router.message(F.photo)
async def handle_photo(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        return
    points = POINTS_CONFIG["photo"]["points"]
    bonus = 0
    if message.caption:
        bonus = POINTS_CONFIG["photo"].get("with_caption", 0)
    total = points + bonus
    await add_points(message.from_user.id, total)
    phrase = random.choice(PHOTO_PHRASES)
    reply = f"<b>{message.from_user.full_name}</b>\n{phrase}\n💎 <b>+{total} баллов</b>"
    await message.reply(reply, parse_mode="HTML")

@router.message(F.video)
async def handle_video(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        return
    points = POINTS_CONFIG["video"]["points"]
    bonus = 0
    if message.caption:
        bonus = POINTS_CONFIG["video"].get("with_caption", 0)
    total = points + bonus
    await add_points(message.from_user.id, total)
    phrase = random.choice(VIDEO_PHRASES)
    reply = f"<b>{message.from_user.full_name}</b>\n{phrase}\n💎 <b>+{total} баллов</b>"
    await message.reply(reply, parse_mode="HTML")

@router.message(F.text & ~F.text.in_([
    "✅ CHECK-IN", "👤 Профиль", "🏆 Топ", "💎 Достижения", "🤝 Реферал", "📋 Задание дня", "💸 Донат", "ℹ️ Команды"
]) & ~F.text.startswith("/"))
async def handle_text(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        return
    words = len(re.findall(r"\\w+", message.text))
    if words < POINTS_CONFIG["text"]["min_words"]:
        return
    points = POINTS_CONFIG["text"]["points"]
    bonus = 0
    if words >= POINTS_CONFIG["text"].get("bonus_words", 50):
        bonus = POINTS_CONFIG["text"].get("bonus_points", 0)
    total = points + bonus
    await add_points(message.from_user.id, total)
    phrase = random.choice(TEXT_PHRASES)
    reply = f"<b>{message.from_user.full_name}</b>\n{phrase}\n💎 <b>+{total} баллов</b>"
    await message.reply(reply, parse_mode="HTML") 
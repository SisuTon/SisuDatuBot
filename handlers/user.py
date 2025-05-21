from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from config.settings import POINTS_CONFIG, SUPER_ADMINS, REQUIRED_SUBSCRIPTIONS
from config.constants import WELCOME_MESSAGE, PHOTO_PHRASES, VIDEO_PHRASES, TEXT_PHRASES, ACHIEVEMENTS
from services.user_service import (
    register_user, get_user_profile, add_user_points,
    get_top_users_list, check_daily_task, check_subscriptions,
    update_user_check_in
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
from handlers.admin import load_allowed_chats

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

@router.message()
async def block_if_not_allowed(message: Message):
    if message.chat.type in ("group", "supergroup"):
        allowed = load_allowed_chats()
        if message.chat.id not in allowed:
            return  # Игнорируем все сообщения в неразрешённых чатах
    # Остальные обработчики будут работать только если чат разрешён

@router.message(F.text == "✅ CHECK-IN")
async def check_in(message: Message):
    """Handle daily check-in"""
    if message.chat.type == "private":
        await message.answer("Чек-ин доступен только в группе!")
        return
    user = await get_user_profile(message.from_user.id)
    if not user:
        await message.answer("Сначала напишите /start")
        return
    points = user.get("points", 0)
    streak = user.get("streak", 0)
    last_check_in = user.get("last_check_in")
    now = datetime.now()
    
    # Проверка на 24-часовой интервал
    if last_check_in:
        try:
            last_check = datetime.fromisoformat(last_check_in)
            time_diff = now - last_check
            if time_diff.total_seconds() < 24 * 3600:  # 24 часа в секундах
                next_check = last_check + timedelta(hours=24)
                await message.answer(
                    f"⏳ Вы уже сделали чек-ин!\nСледующий чек-ин будет доступен после {next_check.strftime('%d.%m %H:%M')}")
                return
        except Exception:
            pass
    
    # Add points and update streak
    points_to_add = POINTS_CONFIG["check_in"]["points"]
    await add_user_points(message.from_user.id, points_to_add, "check_in")
    new_streak = streak + 1 if streak else 1
    
    # Обновляем время последнего чек-ина и серию
    await update_user_check_in(message.from_user.id, new_streak)
    
    await message.answer(
        f"✅ Чек-ин выполнен!\n+{points_to_add} баллов\n🔥 Серия: {new_streak} дней"
    )

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    if message.chat.type == "private":
        # Регистрируем пользователя
        await register_user(message.from_user.id, message.from_user.username)
        
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
    """Обработчик команды /menu"""
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

@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """Обработчик команды /profile"""
    profile = await get_user_profile(message.from_user.id)
    if not profile:
        await message.answer("❌ Профиль не найден")
        return
    
    profile_text = (
        f"👤 Профиль пользователя\n\n"
        f"🏆 Ранг: {profile['rank']['emoji']} {profile['rank']['name']}\n"
        f"💎 Очки: {profile['points']}\n"
        f"🔥 Серия: {profile['streak']} дней\n"
        f"🏅 Достижений: {len(profile['achievements'])}\n"
    )
    
    await message.answer(profile_text, reply_markup=get_profile_keyboard())

@router.message(Command("top"))
async def cmd_top(message: Message):
    """Обработчик команды /top"""
    top_users = await get_top_users_list(10)
    if not top_users:
        await message.answer("❌ Нет данных для отображения топа")
        return
    
    top_text = "🏆 Топ участников:\n\n"
    for i, (user_id, points) in enumerate(top_users, 1):
        top_text += f"{i}. {points} очков\n"
    
    await message.answer(top_text)

@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    user = await get_user_profile(message.from_user.id)
    if not user:
        await message.answer("Сначала напишите /start")
        return
    points = user.get("points", 0)
    streak = user.get("streak", 0)
    tasks_today = user.get("tasks_today", 0)
    text = (
        f"<b>👤 Ваш профиль</b>\n"
        f"Баллы: <b>{points:.1f}</b>\n"
        f"Серия дней: <b>{streak}</b>\n"
        f"Выполнено заданий сегодня: <b>{tasks_today}</b>\n"
    )
    await message.answer(text)

@router.message(F.text == "🏆 Топ")
async def show_top(message: Message):
    top_users = await get_top_users_list(10)
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
    achievements = await get_user_profile(message.from_user.id)
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
    task = await check_daily_task(message.from_user.id)
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
    user = await get_user_profile(callback.from_user.id)
    if not user:
        await callback.answer("Сначала напиши /start", show_alert=True)
        return
    points = POINTS_CONFIG["task"]["points"]
    await add_user_points(callback.from_user.id, points, "daily_task")
    try:
        await callback.message.edit_reply_markup()  # Убираем кнопки
    except Exception:
        pass
    await callback.answer(f"✅ Задание выполнено! +{points} баллов", show_alert=True)

@router.message(F.text == "💸 Задонать себе на будущее!")
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
        "/task — задание дня"
    )

@router.message(Command("task"))
async def cmd_task(message: Message):
    await show_task(message)

@router.message(F.photo)
async def handle_photo(message: Message):
    user = await get_user_profile(message.from_user.id)
    if not user:
        return
    points = POINTS_CONFIG["photo"]["points"]
    bonus = 0
    if message.caption:
        bonus = POINTS_CONFIG["photo"].get("with_caption", 0)
    total = points + bonus
    await add_user_points(message.from_user.id, total, "photo")
    phrase = random.choice(PHOTO_PHRASES)
    reply = f"<b>{message.from_user.full_name}</b>\n{phrase}\n💎 <b>+{total} баллов</b>"
    await message.reply(reply, parse_mode="HTML")

@router.message(F.video)
async def handle_video(message: Message):
    user = await get_user_profile(message.from_user.id)
    if not user:
        return
    points = POINTS_CONFIG["video"]["points"]
    bonus = 0
    if message.caption:
        bonus = POINTS_CONFIG["video"].get("with_caption", 0)
    total = points + bonus
    await add_user_points(message.from_user.id, total, "video")
    phrase = random.choice(VIDEO_PHRASES)
    reply = f"<b>{message.from_user.full_name}</b>\n{phrase}\n💎 <b>+{total} баллов</b>"
    await message.reply(reply, parse_mode="HTML")

@router.message(F.text & ~F.text.in_([
    "✅ CHECK-IN", "👤 Профиль", "🏆 Топ", "💎 Достижения", "🤝 Реферал", "📋 Задание дня", "💸 Задонать себе на будущее!", "ℹ️ Команды"
]) & ~F.text.startswith("/") & ~F.text.lower().startswith("сису") & ~F.text.lower().startswith("sisu"))
async def handle_text(message: Message):
    print(f"USER TEXT HANDLER: {message.text!r}")
    # Проверяем количество слов
    words = message.text.split()
    if len(words) < POINTS_CONFIG["text"]["min_words"]:
        return
    # Начисляем баллы
    points = POINTS_CONFIG["text"]["points"]
    if len(words) >= POINTS_CONFIG["text"]["bonus_words"]:
        points += POINTS_CONFIG["text"]["bonus_points"]
    if await add_user_points(message.from_user.id, points, "text_message"):
        phrase = random.choice(TEXT_PHRASES)
        reply = f"<b>{message.from_user.full_name}</b>\n{phrase}\n💎 <b>+{points} баллов</b>"
        await message.reply(reply, parse_mode="HTML")

@router.message(Command("referral"))
async def referral_cmd(message: Message):
    if message.chat.type == "private":
        return  # Не отвечаем в личке
    await message.answer("Реферальная система скоро будет доступна! Следи за обновлениями.")

@router.message(Command("achievements"))
async def achievements_cmd(message: Message):
    if message.chat.type == "private":
        return  # Не отвечаем в личке
    await message.answer("Раздел достижений скоро появится! Следи за обновлениями 😉")

@router.message(Command("donate"))
async def donate_cmd(message: Message):
    if message.chat.type == "private":
        return  # Не отвечаем в личке
    await message.answer("Задонать себе на будущее! Или поддержи проект тут: https://t.me/your_donate_link") 
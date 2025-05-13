from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from config.settings import SUPER_ADMINS
from database.models import (
    add_points, get_user, get_top_users, set_daily_task,
    get_current_task, update_subscription, get_subscriptions,
    log_admin_action
)
from keyboards.keyboards import get_admin_keyboard
import aiosqlite
from config.settings import DATABASE_PATH
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

def is_super_admin(user_id: int) -> bool:
    """Check if user is super admin"""
    return user_id in SUPER_ADMINS

@router.message(Command("admin"))
async def admin_menu(message: Message):
    """Show admin menu"""
    if not is_super_admin(message.from_user.id):
        return
    
    if message.chat.type != "private":
        await message.answer("Админ-панель доступна только в личном чате с ботом.")
        return
    
    await message.answer(
        "👨‍💼 Админ-панель\n\n"
        "Доступные команды:\n"
        "/broadcast - Рассылка всем пользователям\n"
        "/settask - Установить задание дня\n"
        "/list_users - Список пользователей\n"
        "/addpoints - Начислить баллы\n"
        "/setstreak - Установить серию дней\n"
        "/stats - Статистика бота\n"
        "/setsub - Обновить ссылку подписки\n"
        "/maintenance - Режим обслуживания",
        reply_markup=get_admin_keyboard()
    )

@router.message(F.text == "📢 Рассылка")
async def broadcast_menu(message: Message, state: FSMContext):
    await broadcast_start(message, state)

@router.message(F.text == "👥 Пользователи")
async def users_menu(message: Message):
    """Show users menu"""
    if not is_super_admin(message.from_user.id):
        return
    
    if message.chat.type != "private":
        await message.answer("Управление пользователями доступно только в личном чате с ботом.")
        return
    
    await message.answer(
        "👥 Управление пользователями\n\n"
        "Команды:\n"
        "/list_users - Список пользователей\n"
        "/addpoints @username amount - Начислить баллы\n"
        "/removepoints @username amount - Забрать баллы\n"
        "/setstreak @username days - Установить серию дней\n"
        "/ban @username - Бан пользователя\n"
        "/unban @username - Разбан пользователя"
    )

@router.message(F.text == "📊 Статистика")
async def stats_menu(message: Message):
    """Show statistics"""
    if not is_super_admin(message.from_user.id):
        return
    
    if message.chat.type != "private":
        await message.answer("Статистика доступна только в личном чате с ботом.")
        return
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*), SUM(points), SUM(streak) FROM users"
        ) as cursor:
            row = await cursor.fetchone()
            total_users, total_points, total_streak = row
    
    text = (
        f"📊 <b>Статистика</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Пользователей: <b>{total_users}</b>\n"
        f"Суммарно баллов: <b>{total_points or 0:.1f}</b>\n"
        f"Суммарно серий дней: <b>{total_streak or 0}</b>\n"
    )
    await message.answer(text)

@router.message(F.text == "⚙️ Настройки")
async def settings_menu(message: Message):
    """Show settings menu"""
    if not is_super_admin(message.from_user.id):
        return
    
    if message.chat.type != "private":
        await message.answer("Настройки доступны только в личном чате с ботом.")
        return
    
    await message.answer(
        "⚙️ Настройки\n\n"
        "Команды:\n"
        "/setsub type url - Обновить ссылку подписки\n"
        "/maintenance on|off - Режим обслуживания"
    )

@router.message(F.text == "✏️ Создать задание")
async def admin_create_task(message: Message, state: FSMContext):
    await set_task_start(message, state)

@router.message(F.text == "❌ Отмена")
async def admin_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=get_admin_keyboard())

class BroadcastStates(StatesGroup):
    waiting_for_content = State()
    waiting_for_confirm = State()

broadcast_data = {}

@router.message(Command("broadcast"))
async def broadcast_start(message: Message, state: FSMContext):
    if not is_super_admin(message.from_user.id):
        return
    if message.chat.type != "private":
        await message.answer("Рассылка доступна только в личном чате с ботом.")
        return
    await message.answer("📢 Отправьте сообщение для рассылки (текст, фото, видео или документ с подписью).\nДля отмены — /cancel")
    await state.set_state(BroadcastStates.waiting_for_content)

@router.message(BroadcastStates.waiting_for_content)
async def broadcast_preview(message: Message, state: FSMContext):
    if message.text and message.text.startswith("/cancel"):
        await message.answer("Рассылка отменена.")
        await state.clear()
        return
    # Сохраняем данные рассылки
    data = {}
    if message.photo:
        data['type'] = 'photo'
        data['file_id'] = message.photo[-1].file_id
        data['caption'] = message.caption or ''
        preview = await message.answer_photo(data['file_id'], caption=data['caption'])
    elif message.video:
        data['type'] = 'video'
        data['file_id'] = message.video.file_id
        data['caption'] = message.caption or ''
        preview = await message.answer_video(data['file_id'], caption=data['caption'])
    elif message.document:
        data['type'] = 'document'
        data['file_id'] = message.document.file_id
        data['caption'] = message.caption or ''
        preview = await message.answer_document(data['file_id'], caption=data['caption'])
    elif message.text:
        data['type'] = 'text'
        data['text'] = message.text
        preview = await message.answer(data['text'])
    else:
        await message.answer("Пожалуйста, отправьте текст, фото, видео или документ.")
        return
    broadcast_data[message.from_user.id] = data
    # Клавиатура подтверждения
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить всем", callback_data="broadcast_confirm")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="broadcast_cancel")]
    ])
    await message.answer("Отправить это сообщение всем пользователям?", reply_markup=keyboard)
    await state.set_state(BroadcastStates.waiting_for_confirm)

@router.callback_query(BroadcastStates.waiting_for_confirm, F.data == "broadcast_confirm")
async def broadcast_send(callback: CallbackQuery, state: FSMContext):
    if not is_super_admin(callback.from_user.id):
        return
    data = broadcast_data.get(callback.from_user.id)
    if not data:
        await callback.message.edit_text("Нет данных для рассылки. Попробуйте заново.")
        await state.clear()
        return
    # Получаем всех пользователей
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            user_ids = [row[0] for row in await cursor.fetchall()]
    count = 0
    for uid in user_ids:
        try:
            if data['type'] == 'photo':
                await callback.bot.send_photo(uid, data['file_id'], caption=data['caption'])
            elif data['type'] == 'video':
                await callback.bot.send_video(uid, data['file_id'], caption=data['caption'])
            elif data['type'] == 'document':
                await callback.bot.send_document(uid, data['file_id'], caption=data['caption'])
            elif data['type'] == 'text':
                await callback.bot.send_message(uid, data['text'])
            count += 1
        except:
            pass
    await callback.message.edit_text(f"Рассылка завершена. Доставлено: {count} пользователям.")
    await state.clear()
    broadcast_data.pop(callback.from_user.id, None)

@router.callback_query(BroadcastStates.waiting_for_confirm, F.data == "broadcast_cancel")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Рассылка отменена.")
    await state.clear()
    broadcast_data.pop(callback.from_user.id, None)

@router.message(Command("cancel"), BroadcastStates.waiting_for_content)
async def broadcast_cancel_cmd(message: Message, state: FSMContext):
    await message.answer("Рассылка отменена.")
    await state.clear()
    broadcast_data.pop(message.from_user.id, None)

class TaskStates(StatesGroup):
    waiting_for_content = State()
    waiting_for_points = State()
    waiting_for_publish = State()
    waiting_for_confirm = State()

task_data = {}

@router.message(Command("settask"))
async def set_task_start(message: Message, state: FSMContext):
    if not is_super_admin(message.from_user.id):
        return
    if message.chat.type != "private":
        await message.answer("Управление заданиями доступно только в личном чате с ботом.")
        return
    await message.answer("✏️ Отправьте текст или медиа для нового задания дня. Для отмены — /cancel")
    await state.set_state(TaskStates.waiting_for_content)

@router.callback_query(F.data == "task_new")
async def task_new_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✏️ Отправьте текст или медиа для нового задания дня. Для отмены — /cancel")
    await state.set_state(TaskStates.waiting_for_content)

@router.message(TaskStates.waiting_for_content)
async def task_points_step(message: Message, state: FSMContext):
    if message.text and message.text.startswith("/cancel"):
        await message.answer("Установка задания отменена.")
        await state.clear()
        return
    data = {}
    if message.photo:
        data['type'] = 'photo'
        data['file_id'] = message.photo[-1].file_id
        data['caption'] = message.caption or ''
    elif message.video:
        data['type'] = 'video'
        data['file_id'] = message.video.file_id
        data['caption'] = message.caption or ''
    elif message.document:
        data['type'] = 'document'
        data['file_id'] = message.document.file_id
        data['caption'] = message.caption or ''
    elif message.text:
        data['type'] = 'text'
        data['text'] = message.text
    else:
        await message.answer("Пожалуйста, отправьте текст, фото, видео или документ.")
        return
    task_data[message.from_user.id] = data
    await message.answer("💎 Введите стоимость задания в баллах (только число):")
    await state.set_state(TaskStates.waiting_for_points)

@router.message(TaskStates.waiting_for_points)
async def task_publish_step(message: Message, state: FSMContext):
    if message.text and message.text.startswith("/cancel"):
        await message.answer("Установка задания отменена.")
        await state.clear()
        task_data.pop(message.from_user.id, None)
        return
    try:
        points = int(message.text)
        if points <= 0:
            raise ValueError
    except Exception:
        await message.answer("Пожалуйста, введите положительное целое число для стоимости баллов.")
        return
    task_data[message.from_user.id]['points'] = points
    # Предпросмотр задания с баллами
    data = task_data[message.from_user.id]
    preview_text = f"🐉 <b>Задание дня!</b> 🗡\n\n"
    if data['type'] == 'text':
        preview_text += f"{data['text']}\n\n"
    else:
        preview_text += f"{data['caption']}\n\n"
    preview_text += f"💎 <b>Награда:</b> {points} баллов"
    if data['type'] == 'photo':
        await message.answer_photo(data['file_id'], caption=preview_text, parse_mode="HTML")
    elif data['type'] == 'video':
        await message.answer_video(data['file_id'], caption=preview_text, parse_mode="HTML")
    elif data['type'] == 'document':
        await message.answer_document(data['file_id'], caption=preview_text, parse_mode="HTML")
    else:
        await message.answer(preview_text, parse_mode="HTML")
    # Кнопки выбора публикации
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Только в личку", callback_data="task_personal")],
        [InlineKeyboardButton(text="В личку и в чат", callback_data="task_both")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="task_cancel")]
    ])
    await message.answer("Где опубликовать задание?", reply_markup=keyboard)
    await state.set_state(TaskStates.waiting_for_publish)

@router.callback_query(TaskStates.waiting_for_publish, F.data.in_(["task_personal", "task_both"]))
async def task_confirm_step(callback: CallbackQuery, state: FSMContext):
    data = task_data.get(callback.from_user.id)
    if not data:
        await callback.message.edit_text("Нет данных для задания. Попробуйте заново.")
        await state.clear()
        return
    publish_mode = callback.data
    task_data[callback.from_user.id]['publish_mode'] = publish_mode
    # Кнопки подтверждения
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Установить задание дня", callback_data="task_confirm")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="task_cancel")]
    ])
    await callback.message.answer("Подтвердить установку задания дня?", reply_markup=keyboard)
    await state.set_state(TaskStates.waiting_for_confirm)

@router.callback_query(TaskStates.waiting_for_publish, F.data == "task_cancel")
@router.callback_query(TaskStates.waiting_for_confirm, F.data == "task_cancel")
async def task_cancel_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Установка задания отменена.")
    await state.clear()
    task_data.pop(callback.from_user.id, None)

@router.callback_query(TaskStates.waiting_for_confirm, F.data == "task_confirm")
async def task_confirm_callback(callback: CallbackQuery, state: FSMContext):
    if not is_super_admin(callback.from_user.id):
        return
    data = task_data.get(callback.from_user.id)
    if not data:
        await callback.message.edit_text("Нет данных для задания. Попробуйте заново.")
        await state.clear()
        return
    # Сохраняем задание дня (только текст или caption)
    if data['type'] == 'text':
        task_text = data['text']
    else:
        task_text = data['caption'] or '[Медиа-задание без подписи]'
    points = data.get('points', 0)
    await set_daily_task(f"{task_text}\n\n💎 Награда: {points} баллов", callback.from_user.id)
    # Публикация в чат, если выбрано
    if data.get('publish_mode') == 'task_both':
        chat_id = -1002108698927  # тестовый чат
        preview_text = f"🐉 <b>Задание дня!</b> 🗡\n\n"
        if data['type'] == 'text':
            preview_text += f"{data['text']}\n\n"
        else:
            preview_text += f"{data['caption']}\n\n"
        preview_text += f"💎 <b>Награда:</b> {points} баллов"
        if data['type'] == 'photo':
            await callback.bot.send_photo(chat_id, data['file_id'], caption=preview_text, parse_mode="HTML")
        elif data['type'] == 'video':
            await callback.bot.send_video(chat_id, data['file_id'], caption=preview_text, parse_mode="HTML")
        elif data['type'] == 'document':
            await callback.bot.send_document(chat_id, data['file_id'], caption=preview_text, parse_mode="HTML")
        else:
            await callback.bot.send_message(chat_id, preview_text, parse_mode="HTML")
    await callback.message.edit_text("✅ Задание дня установлено!")
    await state.clear()
    task_data.pop(callback.from_user.id, None)
    await log_admin_action(callback.from_user.id, "settask", f"Текст: {task_text[:100]}")

@router.message(Command("cancel"), TaskStates.waiting_for_content)
@router.message(Command("cancel"), TaskStates.waiting_for_points)
async def task_cancel_cmd(message: Message, state: FSMContext):
    await message.answer("Установка задания отменена.")
    await state.clear()
    task_data.pop(message.from_user.id, None)

@router.message(Command("list_users"))
async def list_users(message: Message):
    """List top users"""
    if not is_super_admin(message.from_user.id):
        return
    
    if message.chat.type != "private":
        await message.answer("Список пользователей доступен только в личном чате с ботом.")
        return
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT user_id, username, points, streak FROM users ORDER BY points DESC LIMIT 20"
        ) as cursor:
            users = await cursor.fetchall()
    
    if not users:
        await message.answer("Нет пользователей в базе.")
        return
    
    text = "<b>Пользователи:</b>\n"
    for uid, uname, pts, streak in users:
        text += f"<code>{uid}</code> @{uname or 'Без ника'} — {pts:.1f} баллов, {streak}🔥\n"
    
    await message.answer(text)

@router.message(Command("addpoints"))
async def add_points_cmd(message: Message):
    """Add points to user"""
    if not is_super_admin(message.from_user.id):
        return
    
    if message.chat.type != "private":
        await message.answer("Начисление баллов доступно только в личном чате с ботом.")
        return
    
    args = message.text.split()
    if len(args) != 3:
        await message.answer("Используйте: /addpoints @username 100")
        return
    
    username, amount = args[1], args[2]
    try:
        amount = float(amount)
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute(
                "SELECT user_id FROM users WHERE username = ?",
                (username.lstrip("@"),)
            ) as cursor:
                user = await cursor.fetchone()
        
        if not user:
            await message.answer("Пользователь не найден.")
            return
        
        await add_points(user[0], amount)
        await message.answer(f"✅ {amount} баллов начислено @{username}")
        await log_admin_action(message.from_user.id, "addpoints", f"@{username}: {amount}")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@router.message(Command("setstreak"))
async def set_streak_cmd(message: Message):
    """Set user streak"""
    if not is_super_admin(message.from_user.id):
        return
    
    if message.chat.type != "private":
        await message.answer("Установка серии дней доступна только в личном чате с ботом.")
        return
    
    args = message.text.split()
    if len(args) != 3:
        await message.answer("Используйте: /setstreak @username 10")
        return
    
    username, days = args[1], args[2]
    try:
        days = int(days)
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                "UPDATE users SET streak = ? WHERE username = ?",
                (days, username.lstrip("@"))
            )
            await db.commit()
        await message.answer(f"✅ Серия дней пользователя @{username} установлена на {days}")
        await log_admin_action(message.from_user.id, "setstreak", f"@{username}: {days}")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@router.message(Command("setsub"))
async def set_sub_cmd(message: Message):
    """Update subscription URL"""
    if not is_super_admin(message.from_user.id):
        return
    
    if message.chat.type != "private":
        await message.answer("Управление подписками доступно только в личном чате с ботом.")
        return
    
    args = message.text.split(maxsplit=2)
    if len(args) != 3:
        await message.answer("Используйте: /setsub type url")
        return
    
    sub_type, url = args[1], args[2]
    await update_subscription(sub_type, url, sub_type)
    await message.answer(f"✅ Ссылка на {sub_type} обновлена!")

@router.message(Command("maintenance"))
async def maintenance_cmd(message: Message):
    """Toggle maintenance mode"""
    if not is_super_admin(message.from_user.id):
        return
    
    if message.chat.type != "private":
        await message.answer("Управление режимом обслуживания доступно только в личном чате с ботом.")
        return
    
    args = message.text.split()
    if len(args) != 2 or args[1] not in ("on", "off"):
        await message.answer("Используйте: /maintenance on | off")
        return
    
    flag_path = "maintenance.flag"
    if args[1] == "on":
        with open(flag_path, "w") as f:
            f.write("maintenance")
        await message.answer("🔧 Режим обслуживания ВКЛЮЧЁН!")
    else:
        import os
        if os.path.exists(flag_path):
            os.remove(flag_path)
        await message.answer("✅ Режим обслуживания ВЫКЛЮЧЕН!")

@router.message(Command("adminlog"))
async def admin_log_cmd(message: Message):
    if not is_super_admin(message.from_user.id):
        return
    if message.chat.type != "private":
        await message.answer("История доступна только в личном чате с ботом.")
        return
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT admin_id, action, details, created_at FROM admin_logs ORDER BY id DESC LIMIT 20"
        ) as cursor:
            logs = await cursor.fetchall()
    if not logs:
        await message.answer("Лог пуст.")
        return
    text = "<b>Последние действия админов:</b>\n\n"
    for admin_id, action, details, created_at in logs:
        text += f"<b>{created_at[:16]}</b> | <code>{admin_id}</code> | <b>{action}</b>\n{details or ''}\n\n"
    await message.answer(text)

@router.message(Command("removepoints"))
async def remove_points_cmd(message: Message):
    """Remove points from user"""
    if not is_super_admin(message.from_user.id):
        return
    if message.chat.type != "private":
        await message.answer("Забор баллов доступен только в личном чате с ботом.")
        return
    args = message.text.split()
    if len(args) != 3:
        await message.answer("Используйте: /removepoints @username 100")
        return
    username, amount = args[1], args[2]
    try:
        amount = float(amount)
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute(
                "SELECT user_id FROM users WHERE username = ?",
                (username.lstrip("@"),)
            ) as cursor:
                user = await cursor.fetchone()
        if not user:
            await message.answer("Пользователь не найден.")
            return
        await add_points(user[0], -amount)
        await message.answer(f"✅ {amount} баллов снято у @{username}")
        await log_admin_action(message.from_user.id, "removepoints", f"@{username}: -{amount}")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@router.message(Command("ban"))
async def ban_user_cmd(message: Message):
    """Ban user"""
    if not is_super_admin(message.from_user.id):
        return
    if message.chat.type != "private":
        await message.answer("Бан доступен только в личном чате с ботом.")
        return
    args = message.text.split()
    if len(args) != 2:
        await message.answer("Используйте: /ban @username")
        return
    username = args[1]
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE users SET is_banned = 1 WHERE username = ?",
            (username.lstrip("@"),)
        )
        await db.commit()
    await message.answer(f"🚫 Пользователь @{username} забанен.")
    await log_admin_action(message.from_user.id, "ban", f"@{username}")

@router.message(Command("unban"))
async def unban_user_cmd(message: Message):
    """Unban user"""
    if not is_super_admin(message.from_user.id):
        return
    if message.chat.type != "private":
        await message.answer("Разбан доступен только в личном чате с ботом.")
        return
    args = message.text.split()
    if len(args) != 2:
        await message.answer("Используйте: /unban @username")
        return
    username = args[1]
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE users SET is_banned = 0 WHERE username = ?",
            (username.lstrip("@"),)
        )
        await db.commit()
    await message.answer(f"✅ Пользователь @{username} разбанен.")
    await log_admin_action(message.from_user.id, "unban", f"@{username}") 
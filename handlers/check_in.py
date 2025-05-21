from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from datetime import datetime, timedelta
from database.models import get_user, update_check_in, add_points
from config.settings import POINTS_CONFIG

router = Router()

@router.callback_query(F.data == "check_in")
async def process_check_in(callback: CallbackQuery):
    """Handle daily check-in"""
    user_id = callback.from_user.id
    user_data = await get_user(user_id)
    
    if not user_data:
        await callback.answer("❌ Профиль не найден", show_alert=True)
        return
        
    _, streak, last_check_in, _, _, _ = user_data
    
    # Проверяем, не делал ли пользователь чек-ин сегодня
    if last_check_in:
        last_check_in_date = datetime.fromisoformat(last_check_in)
        if datetime.now().date() == last_check_in_date.date():
            await callback.answer("❌ Вы уже делали чек-ин сегодня!", show_alert=True)
            return
    
    # Проверяем, не прервалась ли серия
    if last_check_in:
        last_check_in_date = datetime.fromisoformat(last_check_in)
        if datetime.now().date() - last_check_in_date.date() > timedelta(days=1):
            streak = 0
    
    # Увеличиваем серию
    streak += 1
    
    # Начисляем очки
    points = POINTS_CONFIG["check_in"]["points"]
    
    # Добавляем бонусы за серию
    for days, bonus in POINTS_CONFIG["check_in"]["streak_bonus"].items():
        if streak >= days:
            points += bonus
    
    # Обновляем данные
    await update_check_in(user_id, streak)
    await add_points(user_id, points)
    
    # Формируем сообщение
    message = (
        f"✅ Чек-ин выполнен!\n\n"
        f"🔥 Серия: {streak} дней\n"
        f"💎 Получено очков: {points}\n"
    )
    
    # Добавляем информацию о следующем бонусе
    next_bonus = next(
        (days for days in POINTS_CONFIG["check_in"]["streak_bonus"].keys() if days > streak),
        None
    )
    if next_bonus:
        message += f"\n🎯 Следующий бонус через {next_bonus - streak} дней!"
    
    await callback.message.edit_text(message)
    await callback.answer() 
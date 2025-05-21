from datetime import datetime, timedelta
from database.models import (
    add_user, get_user, add_points, get_top_users,
    add_achievement, get_user_achievements, get_current_task,
    get_subscriptions, update_check_in
)
from config.settings import POINTS_CONFIG, RANKS
from config.constants import ACHIEVEMENTS

async def register_user(user_id: int, username: str = None) -> bool:
    """Регистрация нового пользователя"""
    try:
        await add_user(user_id, username)
        return True
    except Exception as e:
        print(f"Error registering user: {e}")
        return False

async def get_user_profile(user_id: int) -> dict:
    """Получение профиля пользователя"""
    user_data = await get_user(user_id)
    if not user_data:
        return None
    
    points, streak, last_check_in, _, _, _ = user_data
    achievements = await get_user_achievements(user_id)
    
    # Определяем ранг пользователя
    current_rank = next((rank for rank in RANKS if points >= rank["min_points"]), RANKS[0])
    
    return {
        "points": points,
        "streak": streak,
        "last_check_in": last_check_in,
        "rank": current_rank,
        "achievements": achievements
    }

async def add_user_points(user_id: int, points: int, reason: str) -> bool:
    """Начисление баллов пользователю"""
    try:
        await add_points(user_id, points)
        # Проверяем достижения
        await check_achievements(user_id)
        return True
    except Exception as e:
        print(f"Error adding points: {e}")
        return False

async def check_achievements(user_id: int) -> list:
    """Проверка и начисление достижений"""
    user_data = await get_user(user_id)
    if not user_data:
        return []
    
    points, streak, _, _, _, _ = user_data
    current_achievements = await get_user_achievements(user_id)
    new_achievements = []
    
    # Проверяем каждое достижение
    for achievement in ACHIEVEMENTS:
        if achievement["id"] not in current_achievements:
            if achievement["type"] == "points" and points >= achievement["requirement"]:
                await add_achievement(user_id, achievement["id"])
                new_achievements.append(achievement)
            elif achievement["type"] == "streak" and streak >= achievement["requirement"]:
                await add_achievement(user_id, achievement["id"])
                new_achievements.append(achievement)
    
    return new_achievements

async def get_top_users_list(limit: int = 10) -> list:
    """Получение списка топ пользователей"""
    try:
        return await get_top_users(limit)
    except Exception as e:
        print(f"Error getting top users: {e}")
        return []

async def check_daily_task(user_id: int) -> dict:
    """Проверка задания дня"""
    try:
        task = await get_current_task()
        if not task:
            return None
        
        return {
            "task": task,
            "points": POINTS_CONFIG["task"]["points"]
        }
    except Exception as e:
        print(f"Error checking daily task: {e}")
        return None

async def check_subscriptions(user_id: int) -> bool:
    """Проверка подписок пользователя"""
    try:
        user_subs = await get_subscriptions(user_id)
        required_subs = set(REQUIRED_SUBSCRIPTIONS)
        return required_subs.issubset(user_subs)
    except Exception as e:
        print(f"Error checking subscriptions: {e}")
        return False

async def update_user_check_in(user_id: int) -> bool:
    """Обновление ежедневной отметки"""
    try:
        await update_check_in(user_id)
        # Начисляем баллы за чек-ин
        await add_points(user_id, POINTS_CONFIG["check_in"]["points"])
        return True
    except Exception as e:
        print(f"Error updating check-in: {e}")
        return False 
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from keyboards.menu import get_main_menu, get_profile_menu
from database.models import get_user, get_user_achievements
from config.settings import RANKS

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command"""
    await message.answer(
        "👋 Привет! Я SisuDatu бот.\n"
        "Я помогу тебе отслеживать активность и зарабатывать очки!",
        reply_markup=get_main_menu()
    )

@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Handle /menu command"""
    await message.answer(
        "📱 Главное меню",
        reply_markup=get_main_menu()
    )

@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """Handle /profile command"""
    user_data = await get_user(message.from_user.id)
    if not user_data:
        await message.answer("❌ Профиль не найден")
        return

    points, streak, last_check_in, _, _, _ = user_data
    achievements = await get_user_achievements(message.from_user.id)
    
    # Определяем ранг пользователя
    current_rank = next((rank for rank in RANKS if points >= rank["min_points"]), RANKS[0])
    
    profile_text = (
        f"👤 Профиль пользователя\n\n"
        f"🏆 Ранг: {current_rank['emoji']} {current_rank['name']}\n"
        f"💎 Очки: {points}\n"
        f"🔥 Серия: {streak} дней\n"
        f"🏅 Достижений: {len(achievements)}\n"
    )
    
    await message.answer(profile_text, reply_markup=get_profile_menu())

@router.callback_query(F.data == "main_menu")
async def process_main_menu(callback: CallbackQuery):
    """Handle main menu button"""
    await callback.message.edit_text(
        "📱 Главное меню",
        reply_markup=get_main_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "profile")
async def process_profile(callback: CallbackQuery):
    """Handle profile button"""
    await cmd_profile(callback.message)
    await callback.answer() 
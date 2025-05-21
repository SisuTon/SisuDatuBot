import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from config.settings import BOT_TOKEN
from database.models import init_db
from handlers import menu, check_in, user, sisu, admin
from aiogram.types import BotCommand

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

# Initialize bot and dispatcher
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Register all routers
dp.include_router(admin.router)
dp.include_router(user.router)
dp.include_router(menu.router)
dp.include_router(check_in.router)
dp.include_router(sisu.router)

async def set_commands(bot):
    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="menu", description="Главное меню"),
        BotCommand(command="profile", description="Ваш профиль"),
        BotCommand(command="top", description="Топ участников"),
        BotCommand(command="task", description="Задание дня"),
        # НЕ добавляем referral, achievements, donate!
    ]
    await bot.set_my_commands(commands)

async def main():
    # Initialize database
    await init_db()
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 
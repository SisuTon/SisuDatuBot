import os
import json
import requests
import random
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from config.settings import BOT_TOKEN
from dotenv import load_dotenv
import re

# Загружаем переменные окружения
load_dotenv()

router = Router()

# Конфигурация для Алисы
ALICE_API_URL = f"https://dialogs.yandex.net/api/v1/skills/{os.getenv('ALICE_SKILL_ID')}/detectIntent"
ALICE_HEADERS = {
    "Authorization": f"OAuth {os.getenv('ALICE_OAUTH_TOKEN')}",
    "Content-Type": "application/json"
}

# Характерные фразы дракона Сису
SISU_PHRASES = [
    "🔥 *рычит по-драконьи* ",
    "💎 *сверкает чешуей* ",
    "🐉 *расправляет крылья* ",
    "✨ *искрит энергией* ",
]

# Криптовалютные термины для вплетения в ответы
CRYPTO_TERMS = [
    "блокчейн", "токены", "NFT", "DeFi", "майнинг", "стейкинг",
    "криптовалюта", "смарт-контракты", "DAO", "Web3"
]

def add_sisu_style(text: str) -> str:
    """Добавляет характерные особенности речи дракона Сису"""
    # Добавляем случайную фразу в начале
    text = random.choice(SISU_PHRASES) + text
    
    # Добавляем характерные окончания
    endings = [" *рычит*", " *сверкает*", " *искрит*"]
    if random.random() < 0.3:  # 30% шанс добавить окончание
        text += random.choice(endings)
    
    return text

def inject_crypto_context(text: str) -> str:
    """Вплетает криптовалютный контекст в ответ"""
    if random.random() < 0.4:  # 40% шанс добавить крипто-контекст
        crypto_term = random.choice(CRYPTO_TERMS)
        text = text.replace(".", f", как {crypto_term}.").replace("!", f", как {crypto_term}!")
    return text

async def get_alice_response(text: str) -> str:
    """Получение ответа от Алисы и его стилизация под Сису"""
    try:
        payload = {
            "query": text,
            "lang": "ru-RU",
            "session": {
                "session_id": "sisu_session",
                "user_id": "sisu_user"
            }
        }
        
        response = requests.post(
            ALICE_API_URL,
            headers=ALICE_HEADERS,
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            base_response = data.get("response", {}).get("text", "Извините, я не смогла обработать ваш запрос.")
            
            # Стилизуем ответ под Сису
            styled_response = add_sisu_style(base_response)
            crypto_response = inject_crypto_context(styled_response)
            
            return crypto_response
        else:
            print(f"Error response from Alice API: {response.text}")
            return add_sisu_style("Произошла ошибка при обращении к моей драконьей мудрости.")
            
    except Exception as e:
        print(f"Error in get_alice_response: {e}")
        return add_sisu_style("Моя драконья мудрость временно недоступна.")

@router.message(Command("sisu"))
async def cmd_sisu(message: Message):
    """Обработчик команды /sisu для общения с драконом Сису"""
    if not message.text:
        return
    
    # Получаем текст после команды /sisu
    query = message.text.replace("/sisu", "").strip()
    if not query:
        await message.answer(
            add_sisu_style(
                "Приветствую, смертный! Я Сису, последний дракон криптомира! "
                "Готова поделиться с тобой своей мудростью о блокчейне и токенах. "
                "Просто напиши свой вопрос после команды /sisu"
            )
        )
        return
    
    # Получаем ответ от Алисы и стилизуем его
    response = await get_alice_response(query)
    
    # Отправляем ответ от имени дракона Сису
    await message.answer(
        f"🐉 {response}",
        parse_mode="HTML"
    )

@router.message(F.text.startswith("Сису,") | F.text.startswith("Сису "))
async def handle_sisu_message(message: Message):
    """Обработчик сообщений, начинающихся с 'Сису'"""
    # Получаем текст после обращения к Сису
    query = message.text.replace("Сису,", "").replace("Сису ", "").strip()
    if not query:
        return
    
    # Получаем ответ от Алисы и стилизуем его
    response = await get_alice_response(query)
    
    # Отправляем ответ от имени дракона Сису
    await message.answer(
        f"🐉 {response}",
        parse_mode="HTML"
    )

@router.message(Command("alice"))
async def cmd_alice(message: Message):
    if not message.text:
        return
    
    # Получаем текст после команды /alice
    query = message.text.replace("/alice", "").strip()
    if not query:
        await message.answer(
            add_sisu_style(
                "Приветствую, смертный! Я Алиса, последняя драконья криптомира! "
                "Готова поделиться с тобой своей мудростью о блокчейне и токенах. "
                "Просто напиши свой вопрос после команды /alice"
            )
        )
        return
    
    # Получаем ответ от Алисы и стилизуем его
    response = await get_alice_response(query)
    
    # Отправляем ответ от имени драконьи Алисы
    await message.answer(
        f"🐉 {response}",
        parse_mode="HTML"
    )

@router.message(F.text.regexp(r"(Алиса|Alice)", flags=re.IGNORECASE))
async def handle_alice_anywhere(message: Message):
    if not message.text:
        return
    
    # Получаем текст после обращения к Алисе
    query = message.text.replace("Алиса,", "").replace("Алиса ", "").strip()
    if not query:
        return
    
    # Получаем ответ от Алисы и стилизуем его
    response = await get_alice_response(query)
    
    # Отправляем ответ от имени драконьи Алисы
    await message.answer(
        f"🐉 {response}",
        parse_mode="HTML"
    ) 
import os
import json
import requests
import random
import time
from collections import defaultdict, deque
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Конфигурация для ЯндексGPT
YANDEXGPT_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
YANDEXART_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync"
API_KEY = os.getenv("YANDEX_API_KEY")
FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")

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

# Храним историю сообщений для каждого пользователя (до 20 сообщений)
user_histories = defaultdict(lambda: deque(maxlen=20))
# Для rate-limit: user_id -> timestamp последнего запроса
user_last_request = defaultdict(float)
RATE_LIMIT_SECONDS = 10  # 1 запрос в 10 секунд

SYSTEM_PROMPT = (
    "Ты — Сису, дракон-эксперт по TON (The Open Network). "
    "Ты дружелюбная, немного саркастичная, но всегда готовая помочь. "
    "Ты знаешь всё про Toncoin, Jettons, NFT, TON Space, TON DNS, TON Storage, TON Sites, TON Proxy, TON Smart Contracts и другие сервисы TON. "
    "Ты объясняешь сложные вещи простым языком, шутишь про токены, блокчейн и AI. "
    "Ты всегда поддерживаешь беседу, помнишь, о чем говорили ранее, и можешь делать отсылки к прошлым сообщениям."
)

def rate_limited(user_id):
    """Проверка rate-limit для пользователя"""
    now = time.time()
    if now - user_last_request[user_id] < RATE_LIMIT_SECONDS:
        return False
    user_last_request[user_id] = now
    return True

def build_messages(user_id, prompt):
    """Сборка сообщений для контекста"""
    messages = [
        {"role": "system", "text": SYSTEM_PROMPT}
    ]
    # Добавляем историю
    for msg in user_histories[user_id]:
        messages.append(msg)
    # Добавляем новый запрос пользователя
    messages.append({"role": "user", "text": prompt})
    return messages

async def yandex_gpt_sisu(user_id, prompt):
    """Получение ответа от ЯндексGPT"""
    headers = {
        "Authorization": f"Api-Key {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 0.8,
            "maxTokens": 200
        },
        "messages": build_messages(user_id, prompt)
    }
    
    response = requests.post(YANDEXGPT_API_URL, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    
    # Сохраняем ответ в историю
    user_histories[user_id].append({"role": "assistant", "text": result["result"]["alternatives"][0]["message"]["text"]})
    
    return result["result"]["alternatives"][0]["message"]["text"]

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

async def get_sisu_response(user_id: int, text: str) -> str:
    """Получение и стилизация ответа от Сису"""
    try:
        # Получаем ответ от ЯндексGPT
        base_response = await yandex_gpt_sisu(user_id, text)
        
        # Стилизуем ответ под Сису
        styled_response = add_sisu_style(base_response)
        crypto_response = inject_crypto_context(styled_response)
        
        return crypto_response
    except Exception as e:
        print(f"Error in get_sisu_response: {e}")
        return add_sisu_style("Моя драконья мудрость временно недоступна. Попробуй позже!")

async def generate_art(prompt: str) -> str:
    """Генерация изображения через Яндекс Art"""
    try:
        headers = {
            "Authorization": f"Api-Key {API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "folderId": FOLDER_ID,
            "modelUri": f"art://{FOLDER_ID}/yandexart/latest",
            "generationOptions": {
                "numImages": 1,
                "seed": 0
            },
            "messages": [
                {"role": "system", "text": "Ты — художник-дракон Сису, рисуешь в стиле магии, TON и мемов."},
                {"role": "user", "text": prompt}
            ]
        }
        
        response = requests.post(YANDEXART_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        # Получаем taskId для асинхронной генерации
        task_id = result["id"]
        
        # Ожидаем результат (polling)
        for _ in range(20):
            time.sleep(2)
            status_resp = requests.get(
                f"https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync/{task_id}",
                headers=headers
            )
            status_resp.raise_for_status()
            status = status_resp.json()
            if status.get("done") and status.get("result"):
                return status["result"]["images"][0]["url"]
        
        return None
    except Exception as e:
        print(f"Error generating art: {e}")
        return None 
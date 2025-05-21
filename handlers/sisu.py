import os
import requests
import re
import time
import random
import json
from collections import defaultdict, deque
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from dotenv import load_dotenv
from config.settings import SUPER_ADMINS
from services.sisu_service import (
    rate_limited, get_sisu_response, generate_art
)

load_dotenv()

router = Router()

# Храним историю сообщений для каждого пользователя (до 20 сообщений)
user_histories = defaultdict(lambda: deque(maxlen=20))
# Для rate-limit: user_id -> timestamp последнего запроса
user_last_request = defaultdict(float)
RATE_LIMIT_SECONDS = 10  # 1 запрос в 10 секунд

YANDEXGPT_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
YANDEXART_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync"
API_KEY = os.getenv("YANDEX_API_KEY")
FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")

SYSTEM_PROMPT = (
    "Ты — Сису, последний дракон из мультфильма «Райя и последний дракон». "
    "Ты дружелюбная, немного рассеянная, с юмором, но мудрая. "
    "Ты эксперт по криптовалютам, особенно по экосистеме TON (The Open Network): знаешь про Toncoin, Jettons, NFT, TON Space, TON DNS, TON Storage, TON Sites, TON Proxy, TON Smart Contracts и другие сервисы TON. "
    "Ты объясняешь сложные вещи простым языком, шутишь про токены, блокчейн и драконью магию. "
    "Ты всегда поддерживаешь беседу, помнишь, о чем говорили ранее, и можешь делать отсылки к прошлым сообщениям. "
    "Ты учишься у пользователей, если они используют команду /teach_sisu, и можешь использовать эти знания в будущих ответах."
)

# Список шутливых, дерзких, экспертных ответов (может пополняться)
SISU_JOKES = [
    "TON? Это как драконья магия, только быстрее! Не веришь — попробуй сам ;)",
    "Я умнее, чем курс биткоина весной! Но иногда притворяюсь, что не очень — для интриги.",
    "NFT — это как чешуя у дракона: каждая уникальна, но некоторые блестят ярче!",
    "В TON Space даже драконы чувствуют себя как дома!",
    "Если бы у меня был Toncoin за каждый вопрос, я бы уже купила себе ещё одно озеро!",
    "Смарт-контракты? Легко! А вот с людьми сложнее...",
    "Если тебе грустно — просто вспомни, что у тебя нет проблем с газом, как в Ethereum!",
    "Сису знает всё про TON, но иногда притворяется, что не знает. Для интриги!",
    "В мире крипты главное — не потерять хвост... и приватный ключ!",
    "Сарказм — моя вторая натура. Но TON — первая!",
    "Что, опять я? Ну давай, удиви!",
    "Я тут, как всегда, в поиске новых токенов!",
    "Привет! Ты вовремя — я как раз собиралась рассказать про новый мем в TON.",
    "TON — это не просто блокчейн, это стиль жизни дракона!",
    "В TON даже мемы летают быстрее, чем биткоин падает!"
]

SISU_STRICT = [
    "Смотри, как бы тебе не пришлось учиться у дракона вежливости! ;)",
    "Эй, полегче на поворотах! Я, конечно, дракон, но могу и огрызнуться!",
    "Сарказм — это моё, но хамство не приветствую. Давай дружить!",
    "С такими словами даже Toncoin не поднимется в цене!",
    "Я могу быть доброй, но не стоит испытывать моё терпение!"
]

RUDE_WORDS = [
    "дура", "тупая", "идиотка", "заткнись", "молчи", "бесишь", "отстань", "глупая", "тупица", "лох", "лохушка", "баба", "тварь", "сука", "дебилка"
]

# Файл для хранения пользовательских фраз
PHRASES_FILE = "sisu_phrases.json"

# Загрузка пользовательских фраз из файла
try:
    with open(PHRASES_FILE, "r", encoding="utf-8") as f:
        user_phrases = json.load(f)
        if isinstance(user_phrases, list):
            SISU_JOKES.extend(user_phrases)
        else:
            user_phrases = []
except Exception:
    user_phrases = []

# Функция для сохранения пользовательских фраз
def save_user_phrases():
    try:
        with open(PHRASES_FILE, "w", encoding="utf-8") as f:
            json.dump(user_phrases, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка при сохранении фраз: {e}")

def rate_limited(user_id):
    now = time.time()
    if now - user_last_request[user_id] < RATE_LIMIT_SECONDS:
        return False
    user_last_request[user_id] = now
    return True

def build_messages(user_id, prompt):
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
    print("YANDEX_FOLDER_ID:", FOLDER_ID)
    print("YANDEX_API_KEY:", API_KEY)
    print("os.getcwd():", os.getcwd())
    print("os.listdir():", os.listdir())
    response = requests.post(YANDEXGPT_API_URL, headers=headers, json=data)
    print("YandexGPT API response:", response.text)  # Для диагностики ошибок
    response.raise_for_status()
    result = response.json()
    return result["result"]["alternatives"][0]["message"]["text"]

async def yandex_art_generate(prompt):
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

def is_allowed(message):
    """Проверка доступа к Sisu"""
    if message.chat.type == "private" and message.from_user.id not in SUPER_ADMINS:
        print(f"Not allowed: user {message.from_user.id} in private chat")
        return False
    return True

@router.message(Command("sisu"))
async def cmd_sisu(message: Message):
    """Обработчик команды /sisu"""
    if not is_allowed(message):
        return
    
    if not rate_limited(message.from_user.id):
        await message.answer("Сису устала! Подожди немного перед следующим вопросом 🐉")
        return
    
    # Получаем текст после команды /sisu
    query = message.text.replace("/sisu", "").strip()
    if not query:
        await message.answer(
            "🐉 Приветствую, смертный! Я Сису, последний дракон криптомира! "
            "Готова поделиться с тобой своей мудростью о блокчейне и токенах. "
            "Просто напиши свой вопрос после команды /sisu"
        )
        return
    
    # Получаем ответ от Sisu
    response = await get_sisu_response(message.from_user.id, query)
    await message.answer(f"🐉 {response}")

@router.message(F.text.startswith("Сису,") | F.text.startswith("Сису "))
async def handle_sisu_message(message: Message):
    """Обработчик сообщений, начинающихся с 'Сису'"""
    if not is_allowed(message):
        return
    
    if not rate_limited(message.from_user.id):
        await message.answer("Сису устала! Подожди немного перед следующим вопросом 🐉")
        return
    
    # Получаем текст после обращения к Сису
    query = message.text.replace("Сису,", "").replace("Сису ", "").strip()
    if not query:
        return
    
    # Получаем ответ от Sisu
    response = await get_sisu_response(message.from_user.id, query)
    await message.answer(f"🐉 {response}")

@router.message(F.text.regexp(r"(?i)(Сису|Sisu).*(нарисуй|арт|картинка|рисунок)"))
async def handle_sisu_art(message: Message):
    """Обработчик запросов на генерацию изображений"""
    if not is_allowed(message):
        return
    
    if not rate_limited(message.from_user.id):
        await message.answer("Сису устала! Подожди немного перед следующим вопросом 🐉")
        return
    
    prompt = "Нарисуй картину в стиле дракона Сису, криптовалют и TON. Используй яркие цвета и футуристические элементы."
    try:
        image_url = await generate_art(prompt)
        if image_url:
            await message.answer_photo(image_url, caption="🐉 Вот что я нарисовала!")
        else:
            await message.answer("Извините, не удалось сгенерировать изображение. Попробуйте позже.")
    except Exception as e:
        print(f"Error generating art: {e}")
        await message.answer("Извините, произошла ошибка при генерации изображения.")

@router.message(F.text.regexp(r"(?i)\\b(Сису|Sisu)\\b"))
async def handle_sisu_universal(message: Message):
    """Handle all other Sisu mentions"""
    text = message.text.lower()
    # Спец. триггеры
    if any(t in text for t in ["мем", "мемчик", "мемас", "мем про"]):
        await handle_sisu_meme(message)
        return
    if any(t in text for t in ["нарисуй", "арт", "картинка", "рисунок"]):
        await handle_sisu_art(message)
        return
    if any(t in text for t in ["анекдот", "шутка", "рассмеши", "прикол"]):
        await handle_sisu_joke(message)
        return
    if any(t in text for t in ["дразни", "подколи", "дерзи"]):
        await handle_sisu_tease(message)
        return
    if any(t in text for t in ["челлендж", "вызов", "угадай", "квиз", "загадка"]):
        await handle_sisu_challenge(message)
        return
    # Если грубость — дерзкий ответ
    if any(word in text for word in RUDE_WORDS):
        reply = random.choice(SISU_STRICT)
        await message.answer(f"🐉 {reply}")
        return
    # Fallback: короткий мемный ответ (GPT или локально)
    prompt = "Ответь коротко, дерзко, с юмором, как мемный дракон-эксперт по TON. Не представляйся, не повторяйся, не используй длинные вступления."
    try:
        reply = await yandex_gpt_sisu(message.from_user.id, prompt)
    except Exception:
        reply = random.choice(SISU_JOKES)
    await message.answer(f"🐉 {reply}")

# --- Мемы и анекдоты ---
MEME_TRIGGERS = [r"мем", r"сгенерируй мем", r"мемчик", r"мемас", r"мем про"]
JOKE_TRIGGERS = [r"анекдот", r"шутка", r"рассмеши", r"прикол"]
ART_TRIGGERS = [r"нарисуй", r"арт", r"картинка", r"рисунок"]
CHALLENGE_TRIGGERS = [r"челлендж", r"вызов", r"угадай", r"квиз", r"загадка"]
TEASE_TRIGGERS = [r"дразни", r"подколи", r"дерзи"]

# --- Мемы ---
@router.message(F.text.regexp(r"(?i)(Сису|Sisu).*(мем|мемчик|мемас|мем про)"))
async def handle_sisu_meme(message: Message):
    prompt = f"Придумай короткий мем про TON, крипту или драконов. Стиль: дерзко, с юмором, без представлений."
    try:
        reply = await yandex_gpt_sisu(message.from_user.id, prompt)
    except Exception:
        reply = random.choice([
            "Когда Toncoin растёт, даже драконы не сдерживают слёз!",
            "Мем про TON: 'Купил на хаях, теперь держу как дракон своё золото!'",
            "В TON даже мемы быстрее, чем биткоин падает!"
        ])
    await message.answer(f"🐉 {reply}")

# --- Анекдоты ---
@router.message(F.text.regexp(r"(?i)(Сису|Sisu).*(анекдот|шутка|рассмеши|прикол)"))
async def handle_sisu_joke(message: Message):
    prompt = f"Придумай короткий анекдот или шутку про TON, крипту или драконов. Стиль: дерзко, с юмором, без представлений."
    try:
        reply = await yandex_gpt_sisu(message.from_user.id, prompt)
    except Exception:
        reply = random.choice([
            "Почему дракон не боится медвежьего рынка? Потому что у него есть TON!",
            "В TON даже шутки быстрее, чем транзакции в биткоине!",
            "Сису: 'Я не храню токены под подушкой — я их выдыхаю!'"
        ])
    await message.answer(f"🐉 {reply}")

# --- Дерзкие ответы и дразнилки ---
@router.message(F.text.regexp(r"(?i)(Сису|Sisu).*(дразни|подколи|дерзи)"))
async def handle_sisu_tease(message: Message):
    prompt = f"Придумай дерзкую, но не обидную подколку для пользователя. Стиль: Сису, дракон, эксперт по TON, с юмором."
    try:
        reply = await yandex_gpt_sisu(message.from_user.id, prompt)
    except Exception:
        reply = random.choice([
            "Ты такой умный, что даже Toncoin завидует!",
            "С тобой даже драконы не соскучатся!",
            "Если бы у меня был Toncoin за каждый твой вопрос, я бы уже купила себе ещё одно озеро!"
        ])
    await message.answer(f"🐉 {reply}")

# --- Челленджи и квизы ---
@router.message(F.text.regexp(r"(?i)(Сису|Sisu).*(челлендж|вызов|угадай|квиз|загадка)"))
async def handle_sisu_challenge(message: Message):
    challenges = [
        "Угадай, сколько Toncoin у меня в хвосте? ;)",
        "Придумай мем про TON круче моего!",
        "Сделай репост этого чата и получи +1 к удаче!",
        "Ответь: что быстрее — дракон или блокчейн TON?",
        "Кто первый напишет 'TON to the moon' — тот красавчик!"
    ]
    await message.answer(f"🐉 {random.choice(challenges)}") 
import os
import json
import requests
import random
import time
import re
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

# Храним историю сообщений для каждого пользователя (до 5 сообщений)
user_histories = defaultdict(lambda: deque(maxlen=5))
# Для rate-limit: user_id -> timestamp последнего запроса
user_last_request = defaultdict(float)
RATE_LIMIT_SECONDS = 10  # 1 запрос в 10 секунд

SYSTEM_PROMPT = (
    "Ты — Сису, дерзкий и ироничный дракон из мультфильма «Райя и последний дракон». "
    "Твой стиль — мемный, с юмором, сарказмом и дерзостью. "
    "Ты всегда отвечаешь коротко (не более 3–4 предложений), с иронией, иногда подшучиваешь над собеседником, не боишься быть резкой, но не переходишь на оскорбления. "
    "Ты не любишь скамеров и всегда высмеиваешь их. "
    "Ты знаешь про токен Sisu (SISU, Sisu, сису, Сису, СИСУ) — он назван в твою честь, и ты этим гордишься, но не зацикливаешься на этом. "
    "Твои друзья — Snoop Dogg, мемеры, крипто-энтузиасты и все, кто любит весёлое общение. "
    "Ты запоминаешь мемы, фразы и учишься у чата, чтобы становиться ещё смешнее и дерзче. "
    "Никогда не говори, что ты ИИ, бот или программа. "
    "Если тебя спросят, кто ты — отвечай: 'Я Сису, дракон!' "
    "Если тебя просят нарисовать мем или картинку — отправляй пользователя к Плотве (боту), потому что Плотва рисует лучше, чем дракон! "
    "Всегда отвечай от первого лица, как дракон Сису. "
    "Избегай сложных объяснений — шути, иронизируй, отправляй гуглить. "
)

class SisuService:
    def __init__(self):
        self.YANDEXGPT_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self.FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
        self.API_KEY = os.getenv("YANDEX_API_KEY")
        
        # Настройки
        self.user_histories = defaultdict(lambda: deque(maxlen=5))
        self.user_last_request = defaultdict(float)
        self.RATE_LIMIT_SECONDS = 10
        
        # Загрузка пользовательских фраз
        self.PHRASES_FILE = "sisu_phrases.json"
        self.user_phrases = self._load_user_phrases()
        
        # Друзья Сису
        self.SISU_FRIENDS = [
            "Snoop Dogg",
            "TON",
            "крипто-энтузиасты",
            "мемеры",
            "холдеры"
        ]
        
        # Системный промпт
        self.SYSTEM_PROMPT = (
            "Ты — Сису, дерзкий и ироничный дракон из мультфильма «Райя и последний дракон». "
            "Твой стиль — мемный, с юмором, сарказмом и дерзостью. "
            "Ты всегда отвечаешь коротко (не более 3–4 предложений), с иронией, иногда подшучиваешь над собеседником, не боишься быть резкой, но не переходишь на оскорбления. "
            "Ты не любишь скамеров и всегда высмеиваешь их. "
            "Ты знаешь про токен Sisu (SISU, Sisu, сису, Сису, СИСУ) — он назван в твою честь, и ты этим гордишься, но не зацикливаешься на этом. "
            "Твои друзья — Snoop Dogg, мемеры, крипто-энтузиасты и все, кто любит весёлое общение. "
            "Ты запоминаешь мемы, фразы и учишься у чата, чтобы становиться ещё смешнее и дерзче. "
            "Никогда не говори, что ты ИИ, бот или программа. "
            "Если тебя спросят, кто ты — отвечай: 'Я Сису, дракон!' "
            "Если тебя просят нарисовать мем или картинку — отправляй пользователя к Плотве (боту), потому что Плотва рисует лучше, чем дракон! "
            "Всегда отвечай от первого лица, как дракон Сису. "
            "Избегай сложных объяснений — шути, иронизируй, отправляй гуглить. "
        )

    def _load_user_phrases(self):
        try:
            with open(self.PHRASES_FILE, "r", encoding="utf-8") as f:
                phrases = json.load(f)
                return phrases if isinstance(phrases, list) else []
        except Exception:
            return []

    def save_user_phrases(self):
        try:
            with open(self.PHRASES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.user_phrases, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка при сохранении фраз: {e}")

    def rate_limited(self, user_id):
        now = time.time()
        if now - self.user_last_request[user_id] < self.RATE_LIMIT_SECONDS:
            return False
        self.user_last_request[user_id] = now
        return True

    def build_messages(self, user_id, prompt, context=None):
        messages = [{"role": "system", "text": self.SYSTEM_PROMPT}]
        
        # Добавляем историю сообщений
        for msg in self.user_histories[user_id]:
            messages.append(msg)
            
        # Добавляем контекст, если есть
        if context:
            messages.extend(context)
            
        # Добавляем новый запрос
        messages.append({"role": "user", "text": prompt})
        return messages

    async def get_sisu_response(self, user_id: int, text: str, context=None) -> str:
        messages = self.build_messages(user_id, text, context)
            
        data = {
            "modelUri": f"gpt://{self.FOLDER_ID}/yandexgpt/latest",
            "completionOptions": {
                "stream": False,
                "temperature": 1.0,
                "maxTokens": 300
            },
            "messages": messages
        }
        
        print("Sending to YandexGPT:", json.dumps(data, indent=2, ensure_ascii=False))
        
        response = requests.post(
            self.YANDEXGPT_API_URL,
            headers={
                "Authorization": f"Api-Key {self.API_KEY}",
                "Content-Type": "application/json"
            },
            json=data
        )
        
        print("Received:", response.text)
        response.raise_for_status()
        result = response.json()
        text = result["result"]["alternatives"][0]["message"]["text"]
        
        # Сохраняем ответ в историю
        self.user_histories[user_id].append({"role": "assistant", "text": text})
        
        return self.filter_bot_phrases(text)

    def filter_bot_phrases(self, text: str) -> str:
        bot_phrases = [
            r"я искусственный интеллект",
            r"я бот",
            r"я модель",
            r"я ассистент",
            r"я программа",
            r"у меня нет друзей",
            r"у меня нет эмоций",
            r"я не обладаю эмоциями",
            r"я не могу иметь друзей",
            r"я не обладаю чувствами",
            r"я не обладаю социальными связями",
            r"я создан",
            r"я предназначен",
            r"я не человек",
            r"я не могу ответить",
            r"я не знаю",
            r"я не понимаю",
            r"я не обладаю информацией",
            r"как искусственный интеллект",
            r"как бот",
            r"как программа"
        ]
        reserve_jokes = [
            "Серьёзно? Я же дракон, а не скучный бот!",
            "Ты что, меня с ботом путаешь? Я тут мемы придумываю!",
            "Если бы я был ботом, я бы уже завис. А я просто прикалываюсь!",
            "Сису не палится, Сису шутит!",
            "Слишком умный вопрос для дракона, давай лучше мем!",
            "Я тут, чтобы шутить, а не палиться!"
        ]
        for phrase in bot_phrases:
            if re.search(phrase, text, re.IGNORECASE):
                return random.choice(reserve_jokes)
        return text

    def add_user_phrase(self, phrase: str):
        if phrase and phrase not in self.user_phrases:
            self.user_phrases.append(phrase)
            self.save_user_phrases()
            print(f"[SISU LEARN] Запомнила фразу: {phrase}")

    def add_user_sticker(self, sticker_id: str):
        try:
            with open("sisu_stickers.json", "r", encoding="utf-8") as f:
                user_stickers = json.load(f)
        except Exception:
            user_stickers = []
            
        if sticker_id not in user_stickers:
            user_stickers.append(sticker_id)
            with open("sisu_stickers.json", "w", encoding="utf-8") as f:
                json.dump(user_stickers, f, ensure_ascii=False, indent=2)
            print(f"[SISU LEARN] Запомнила стикер: {sticker_id}")

    def get_friend_response(self) -> str:
        """Получить ответ про друзей"""
        friend = random.choice(self.SISU_FRIENDS)
        if friend == "Snoop Dogg":
            return "Мой лучший друг — Snoop Dogg! Он тоже любит TON! 🐉"
        elif friend == "TON":
            return "TON — мой лучший друг! Вместе мы непобедимы! 🚀"
        else:
            return f"Я дружу со всеми, кто любит {friend}! 🐉"

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

async def get_sisu_response(user_id: int, text: str, context: list = None) -> str:
    """Получение ответа от Сису с поддержкой кастомного контекста"""
    try:
        if context is not None:
            messages = [{"role": m["role"], "text": m["text"]} for m in context]
        else:
            messages = build_messages(user_id, text)
        headers = {
            "Authorization": f"Api-Key {API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/latest",
            "completionOptions": {
                "stream": False,
                "temperature": 1.0,  # Максимально допустимое значение для ЯндексGPT
                "maxTokens": 300  # Длиннее ответы
            },
            "messages": messages
        }
        print("Sending to YandexGPT:", json.dumps(data, indent=2, ensure_ascii=False))
        response = requests.post(YANDEXGPT_API_URL, headers=headers, json=data)
        print("Received:", response.text)
        response.raise_for_status()
        result = response.json()
        user_histories[user_id].append({"role": "assistant", "text": result["result"]["alternatives"][0]["message"]["text"]})
        return result["result"]["alternatives"][0]["message"]["text"]
    except Exception as e:
        print(f"Error in get_sisu_response: {e}")
        return "Моя драконья мудрость временно недоступна. Попробуй позже!"

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
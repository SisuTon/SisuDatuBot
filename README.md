# SisuDatuBot

Бот активности для Telegram, который мотивирует пользователей к взаимодействию в чате.

## Возможности

- ✅ Начисление баллов за активность
- 🏆 Рейтинг участников
- 🎯 Задания дня
- 🤝 Реферальная программа
- 💎 Достижения
- 👑 Админ-панель

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/SisuDatuBot.git
cd SisuDatuBot
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` и добавьте в него токен бота:
```
BOT_TOKEN=your_bot_token_here
```

## Запуск

```bash
python main.py
```

## Админ-команды

- `/admin` - открыть админ-панель
- `/list_users` - список пользователей
- `/addpoints @username amount` - начислить баллы
- `/setstreak @username days` - установить серию дней
- `/broadcast text` - рассылка всем пользователям
- `/stats` - статистика бота
- `/settask text` - установить задание дня
- `/setsub type url` - обновить ссылку подписки
- `/maintenance on|off` - режим обслуживания

## Структура проекта

```
SisuDatuBot/
├── config/
│   ├── settings.py
│   └── constants.py
├── database/
│   └── models.py
├── handlers/
│   ├── admin.py
│   └── user.py
├── keyboards/
│   └── keyboards.py
├── requirements.txt
└── main.py
```

## Лицензия

MIT 
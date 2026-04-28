import os
from dotenv import load_dotenv

load_dotenv()

_token = os.getenv("BOT_TOKEN")

if _token is None:
    raise ValueError(
        "Токен не найден! Создайте файл .env с BOT_TOKEN=ваш_токен"
    )

BOT_TOKEN: str = _token

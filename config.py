import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

_token = os.getenv("BOT_TOKEN")
if _token is None:
    raise ValueError(
        "Токен не найден! Создайте файл .env с BOT_TOKEN=ваш_токен"
    )
BOT_TOKEN: str = _token

_admin_group = os.getenv("ADMIN_GROUP_ID")
if _admin_group is None:
    raise ValueError("ID группы не найден! Добавьте ADMIN_GROUP_ID в .env")
ADMIN_GROUP_ID: int = int(_admin_group)

DATA_DIR = Path("/app/data")
if not DATA_DIR.exists():
    DATA_DIR = Path("data")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = str(DATA_DIR / "bot.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"
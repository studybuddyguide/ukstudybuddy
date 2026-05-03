import asyncio
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import init_db, get_db
from handlers.start import start_router
from handlers.contact import contact_router
from handlers.favorites import favorites_router
from handlers.admin import admin_router
from data.seed import seed_schools

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(start_router)
dp.include_router(contact_router)
dp.include_router(favorites_router)
dp.include_router(admin_router)


async def main():
    await init_db()
    print("База данных готова!")

    # Проверяем и заполняем школы при первом запуске
    db = await get_db()
    try:
        cursor = await db.execute("SELECT COUNT(*) FROM schools")
        count = (await cursor.fetchone())[0]
        if count == 0:
            print("Школ нет — заполняем БД...")
            await db.close()
            await seed_schools()
        else:
            print(f"Школ в БД: {count}")
    finally:
        await db.close()

    print("Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
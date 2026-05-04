import asyncio
import json
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import init_db, get_db
from handlers.start import start_router
from handlers.contact import contact_router

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(start_router)
dp.include_router(contact_router)


SCHOOLS_DATA = [
    {
        "name": "Kaplan International",
        "city": "Лондон",
        "price_per_week": 350,
        "rating": 4.8,
        "age_group": "👨 Взрослым",
        "durations": ["Краткосрочный", "Среднесрочный", "Долгосрочный"],
        "description": "Одна из крупнейших сетей языковых школ. Современные классы, отличное расположение в центре Лондона.",
    },
    {
        "name": "EC English",
        "city": "Лондон",
        "price_per_week": 290,
        "rating": 4.7,
        "age_group": "👨 Взрослым",
        "durations": ["Краткосрочный", "Среднесрочный"],
        "description": "Уютная школа в районе Ковент-Гарден. Сильный разговорный уклон.",
    },
    {
        "name": "St Giles International",
        "city": "Лондон",
        "price_per_week": 320,
        "rating": 4.6,
        "age_group": "👨 Взрослым",
        "durations": ["Среднесрочный", "Долгосрочный"],
        "description": "Подготовка к IELTS и Cambridge экзаменам. Высокий процент сдачи.",
    },
    {
        "name": "LSI London",
        "city": "Лондон",
        "price_per_week": 270,
        "rating": 4.5,
        "age_group": "👨 Взрослым",
        "durations": ["Краткосрочный", "Среднесрочный"],
        "description": "Бюджетный вариант в центре Лондона. Малые группы до 10 человек.",
    },
    {
        "name": "British Study Centres",
        "city": "Лондон",
        "price_per_week": 310,
        "rating": 4.7,
        "age_group": "🧒 Детям",
        "durations": ["Краткосрочный", "Среднесрочный"],
        "description": "Летние и каникулярные программы для детей и подростков. Насыщенная культурная программа.",
    },
    {
        "name": "Kids Unlimited",
        "city": "Лондон",
        "price_per_week": 400,
        "rating": 4.9,
        "age_group": "🧒 Детям",
        "durations": ["Краткосрочный"],
        "description": "Премиальные детские программы. Проживание в резиденции, спорт, экскурсии.",
    },
]


async def seed_schools():
    db = await get_db()
    try:
        for school_data in SCHOOLS_DATA:
            durations_json = json.dumps(school_data["durations"], ensure_ascii=False)
            await db.execute(
                "INSERT INTO schools (name, city, price_per_week, rating, age_group, durations, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    school_data["name"],
                    school_data["city"],
                    school_data["price_per_week"],
                    school_data["rating"],
                    school_data["age_group"],
                    durations_json,
                    school_data["description"],
                ),
            )
        await db.commit()
    finally:
        await db.close()


async def main():
    await init_db()

    db = await get_db()
    try:
        cursor = await db.execute("SELECT COUNT(*) FROM schools")
        count = (await cursor.fetchone())[0]
        if count == 0:
            await db.close()
            await seed_schools()
    finally:
        await db.close()

    print("Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
import asyncio
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from handlers.start import start_router

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(start_router)


async def main():
    print("Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

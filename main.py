import asyncio
import os
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN, DATABASE_PATH, DATA_DIR
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
    # Отправляем отладку в группу
    debug_msg = f"🔧 BOT STARTED\nDATA_DIR={DATA_DIR}\nexists={DATA_DIR.exists()}\nDB_PATH={DATABASE_PATH}"
    try:
        await bot.send_message(chat_id=int(os.getenv("ADMIN_GROUP_ID")), text=debug_msg)
    except Exception:
        pass

    await init_db()
    
    db = await get_db()
    try:
        cursor = await db.execute("SELECT COUNT(*) FROM schools")
        count = (await cursor.fetchone())[0]
        
        if count == 0:
            await db.close()
            await seed_schools()
            db = await get_db()
            cursor = await db.execute("SELECT COUNT(*) FROM schools")
            count = (await cursor.fetchone())[0]
        
        await bot.send_message(
            chat_id=int(os.getenv("ADMIN_GROUP_ID")),
            text=f"🔧 Schools in DB: {count}"
        )
    except Exception as e:
        await bot.send_message(
            chat_id=int(os.getenv("ADMIN_GROUP_ID")),
            text=f"🔧 DB ERROR: {e}"
        )
    finally:
        await db.close()

    await bot.send_message(
        chat_id=int(os.getenv("ADMIN_GROUP_ID")),
        text="✅ Bot is ready!"
    )
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
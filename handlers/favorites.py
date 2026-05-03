from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from database import get_db

favorites_router = Router()


@favorites_router.message(lambda msg: msg.text == "⭐ Избранное")
async def show_favorites(message: types.Message, state: FSMContext):
    await state.clear()
    if not message.from_user:
        return

    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT s.name, s.city, s.price_per_week, s.rating
            FROM favorites f
            JOIN schools s ON f.school_id = s.id
            WHERE f.user_id = ?
            """,
            (message.from_user.id,),
        )
        favorites = await cursor.fetchall()
    finally:
        await db.close()

    if not favorites:
        await message.answer(
            "⭐ У тебя пока нет избранных школ.\n\n"
            "Нажми «🔍 Подобрать курс», чтобы найти школу и добавить в избранное."
        )
        return

    text = "⭐ Твои избранные школы:\n\n"
    for i, fav in enumerate(favorites, 1):
        fav = dict(fav)
        text += (
            f"{i}. 🏫 {fav['name']}\n"
            f"   📍 {fav['city']}\n"
            f"   💰 £{fav['price_per_week']}/нед\n"
            f"   ⭐ {fav['rating']}/5\n\n"
        )

    await message.answer(text)
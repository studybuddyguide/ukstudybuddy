from aiogram import Router, types
from sqlalchemy import select

from database import async_session
from models import User, School, Favorite

favorites_router = Router()


@favorites_router.message(lambda msg: msg.text == "⭐ Избранное")
async def show_favorites(message: types.Message):
    if not message.from_user:
        return

    async with async_session() as session:
        result = await session.execute(
            select(Favorite).where(Favorite.user_id == message.from_user.id)
        )
        favorites = list(result.scalars().all())

    if not favorites:
        await message.answer(
            "⭐ У тебя пока нет избранных школ.\n\n"
            "Нажми «🔍 Подобрать курс», чтобы найти школу и добавить в избранное."
        )
        return

    text = "⭐ Твои избранные школы:\n\n"
    for i, fav in enumerate(favorites, 1):
        school = fav.school
        text += (
            f"{i}. 🏫 {school.name}\n"
            f"   📍 {school.city}\n"
            f"   💰 £{school.price_per_week}/нед\n"
            f"   ⭐ {school.rating}/5\n\n"
        )

    await message.answer(text)
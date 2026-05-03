from datetime import datetime, timedelta

from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy import select, func

from database import async_session
from models import User, SearchHistory
from config import ADMIN_GROUP_ID

admin_router = Router()


@admin_router.message(Command("stats"))
async def show_stats(message: types.Message):
    if message.chat.id != ADMIN_GROUP_ID:
        return

    async with async_session() as session:
        total_result = await session.execute(
            select(func.count(User.id))
        )
        total_users = total_result.scalar()

        week_ago = datetime.utcnow() - timedelta(days=7)

        active_result = await session.execute(
            select(func.count(func.distinct(SearchHistory.user_id)))
            .where(SearchHistory.created_at >= week_ago)
        )
        active_users = active_result.scalar()

        subscribed_result = await session.execute(
            select(func.count(User.id)).where(User.is_subscribed == True)
        )
        subscribed = subscribed_result.scalar()

    await message.answer(
        f"📊 Статистика бота:\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"📅 Активных за неделю: {active_users}\n"
        f"🔔 Подписано на рассылку: {subscribed}"
    )


@admin_router.message(Command("broadcast"))
async def broadcast_start(message: types.Message):
    if message.chat.id != ADMIN_GROUP_ID:
        return

    text = message.text
    if text == "/broadcast":
        await message.answer(
            "📢 Чтобы сделать рассылку, напиши:\n"
            "`/broadcast Текст сообщения`"
        )
        return

    broadcast_text = text.replace("/broadcast ", "", 1)

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.is_subscribed == True)
        )
        users = list(result.scalars().all())

    success = 0
    failed = 0

    for user in users:
        try:
            await message.bot.send_message(user.id, f"📢 Рассылка:\n\n{broadcast_text}")
            success += 1
        except Exception:
            failed += 1

    await message.answer(
        f"✅ Рассылка завершена:\n"
        f"Отправлено: {success}\n"
        f"Не удалось: {failed}"
    )


@admin_router.message(Command("unsubscribe"))
async def unsubscribe(message: types.Message):
    if not message.from_user:
        return

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

        if user:
            user.is_subscribed = False
            await session.commit()

    await message.answer(
        "🔕 Ты отписался от рассылки.\n\n"
        "Чтобы снова подписаться — нажми /subscribe"
    )


@admin_router.message(Command("subscribe"))
async def subscribe(message: types.Message):
    if not message.from_user:
        return

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
            )
            session.add(user)
        else:
            user.is_subscribed = True

        await session.commit()

    await message.answer(
        "🔔 Ты подписался на рассылку!\n\n"
        "Буду присылать тебе новости о скидках и новых школах."
    )
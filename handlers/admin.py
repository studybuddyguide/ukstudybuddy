from datetime import datetime, timedelta
from aiogram import Router, types
from aiogram.filters import Command
from config import ADMIN_GROUP_ID
from database import get_db

admin_router = Router()


@admin_router.message(Command("stats"))
async def show_stats(message: types.Message):
    if message.chat.id != ADMIN_GROUP_ID:
        return

    db = await get_db()
    try:
        total = await db.execute("SELECT COUNT(*) FROM users")
        total_users = (await total.fetchone())[0]

        week_ago = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        active = await db.execute(
            "SELECT COUNT(DISTINCT user_id) FROM search_history WHERE created_at >= ?",
            (week_ago,),
        )
        active_users = (await active.fetchone())[0]

        sub = await db.execute("SELECT COUNT(*) FROM users WHERE is_subscribed = 1")
        subscribed = (await sub.fetchone())[0]
    finally:
        await db.close()

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
        await message.answer("📢 Чтобы сделать рассылку, напиши:\n`/broadcast Текст сообщения`")
        return

    broadcast_text = text.replace("/broadcast ", "", 1)

    db = await get_db()
    try:
        cursor = await db.execute("SELECT id FROM users WHERE is_subscribed = 1")
        users = await cursor.fetchall()
    finally:
        await db.close()

    success = 0
    failed = 0

    for user in users:
        try:
            await message.bot.send_message(user[0], f"📢 Рассылка:\n\n{broadcast_text}")
            success += 1
        except Exception:
            failed += 1

    await message.answer(f"✅ Рассылка завершена:\nОтправлено: {success}\nНе удалось: {failed}")


@admin_router.message(Command("unsubscribe"))
async def unsubscribe(message: types.Message):
    if not message.from_user:
        return

    db = await get_db()
    try:
        await db.execute("UPDATE users SET is_subscribed = 0 WHERE id = ?", (message.from_user.id,))
        await db.commit()
    finally:
        await db.close()

    await message.answer("🔕 Ты отписался от рассылки.\n\nЧтобы снова подписаться — нажми /subscribe")


@admin_router.message(Command("subscribe"))
async def subscribe(message: types.Message):
    if not message.from_user:
        return

    db = await get_db()
    try:
        user = await db.execute("SELECT id FROM users WHERE id = ?", (message.from_user.id,))
        row = await user.fetchone()
        if row is None:
            await db.execute(
                "INSERT INTO users (id, username, first_name, last_name, is_subscribed) VALUES (?, ?, ?, ?, 1)",
                (message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name),
            )
        else:
            await db.execute("UPDATE users SET is_subscribed = 1 WHERE id = ?", (message.from_user.id,))
        await db.commit()
    finally:
        await db.close()

    await message.answer("🔔 Ты подписался на рассылку!\n\nБуду присылать тебе новости о скидках и новых школах.")

@admin_router.message(Command("users"))
async def show_users(message: types.Message):
    if message.chat.id != ADMIN_GROUP_ID:
        return

    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, username, first_name, last_name, created_at FROM users ORDER BY created_at DESC LIMIT 20"
        )
        users = await cursor.fetchall()
    finally:
        await db.close()

    if not users:
        await message.answer("👥 Пока нет пользователей.")
        return

    text = f"👥 Последние 20 пользователей:\n\n"
    for user in users:
        username = f"@{user[1]}" if user[1] else "нет username"
        name = f"{user[2] or ''} {user[3] or ''}".strip() or "без имени"
        text += f"• {name} | {username} | ID: {user[0]}\n"

    await message.answer(text)
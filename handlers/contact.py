from aiogram import Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_GROUP_ID
from database import get_db

contact_router = Router()


class ContactStates(StatesGroup):
    waiting_for_message = State()


async def get_or_create_topic(bot, user_id: int, user_info: str, username: str) -> int:
    """Возвращает thread_id для пользователя. Если темы нет или она удалена — создаёт новую."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT thread_id FROM user_topics WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()

        if row is not None:
            old_thread_id = row[0]
            try:
                check_msg = await bot.send_message(
                    ADMIN_GROUP_ID,
                    ".",
                    message_thread_id=old_thread_id
                )
                await check_msg.delete()
                return old_thread_id
            except TelegramBadRequest:
                pass

        topic = await bot.create_forum_topic(
            chat_id=ADMIN_GROUP_ID,
            name=f"{user_info} ({username})"
        )
        thread_id = topic.message_thread_id

        if row is not None:
            await db.execute(
                "UPDATE user_topics SET thread_id = ? WHERE user_id = ?",
                (thread_id, user_id),
            )
        else:
            await db.execute(
                "INSERT INTO user_topics (user_id, thread_id, username, first_name) VALUES (?, ?, ?, ?)",
                (user_id, thread_id, username, user_info),
            )
        await db.commit()

        return thread_id
    finally:
        await db.close()


@contact_router.message(lambda msg: msg.text == "📩 Связаться с нами")
async def contact_start(message: types.Message, state: FSMContext):
    await message.answer(
        "📩 Напиши свой вопрос прямо сюда — "
        "я перешлю его команде, и мы ответим в ближайшее время.\n\n"
        "Для отмены нажми /cancel"
    )
    await state.set_state(ContactStates.waiting_for_message)


@contact_router.message(ContactStates.waiting_for_message)
async def contact_forward(message: types.Message, state: FSMContext):
    if message.from_user is None:
        await message.answer("❌ Не удалось отправить. Попробуй позже.")
        await state.clear()
        return

    user = message.from_user
    user_info = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = f"@{user.username}" if user.username else "нет username"

    thread_id = await get_or_create_topic(message.bot, user.id, user_info, username)

    await message.forward(ADMIN_GROUP_ID, message_thread_id=thread_id)

    await message.answer("✅ Твой вопрос отправлен! Мы ответим в ближайшее время.")
    await state.clear()


@contact_router.message(Command("cancel"))
async def contact_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отправка вопроса отменена.")


@contact_router.message(lambda msg: msg.reply_to_message is not None)
async def admin_reply(message: types.Message):
    """Админ отвечает в теме — бот пересылает ответ пользователю."""
    if message.chat.id != ADMIN_GROUP_ID:
        return

    thread_id = message.message_thread_id
    if thread_id is None:
        return

    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT user_id FROM user_topics WHERE thread_id = ?",
            (thread_id,),
        )
        row = await cursor.fetchone()
    finally:
        await db.close()

    if row is None:
        return

    user_id = row[0]

    try:
        await message.bot.send_message(
            user_id,
            f"📩 Ответ от команды UK Study Buddy:\n\n{message.text}"
        )
        await message.reply("✅ Ответ отправлен пользователю.")
    except Exception:
        await message.reply("❌ Не удалось отправить ответ.")


@contact_router.message(lambda msg: msg.chat.type == "private" and msg.text not in [
    "🔍 Подобрать курс", "🏫 Наши школы", "💰 Скидки", "⭐ Избранное", "📩 Связаться с нами",
    "/start", "/subscribe", "/unsubscribe", "/cancel", "/stats", "/broadcast", "/users"
])
async def handle_regular_message(message: types.Message):
    """Пересылает только обычные сообщения, не команды и не кнопки меню."""
    if message.from_user is None:
        return

    user_id = message.from_user.id
    user_info = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
    username = f"@{message.from_user.username}" if message.from_user.username else "нет username"

    thread_id = await get_or_create_topic(message.bot, user_id, user_info, username)

    await message.forward(ADMIN_GROUP_ID, message_thread_id=thread_id)

    await message.answer("✅ Сообщение отправлено команде!")
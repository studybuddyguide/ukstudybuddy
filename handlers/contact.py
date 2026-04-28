from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_GROUP_ID

contact_router = Router()

pending_questions: dict[int, int] = {}


class ContactStates(StatesGroup):
    waiting_for_message = State()


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
        user_info = "Неизвестный пользователь"
        username = "нет username"
        user_id = 0
    else:
        user = message.from_user
        user_info = (
            f"{user.first_name or ''} {user.last_name or ''}".strip()
        )
        username = f"@{user.username}" if user.username else "нет username"
        user_id = user.id

    forwarded = await message.bot.send_message(
        ADMIN_GROUP_ID,
        f"📩 Вопрос от пользователя:\n"
        f"Имя: {user_info}\n"
        f"Username: {username}\n"
        f"ID: {user_id}\n\n"
        f"Текст:\n{message.text}\n\n"
        f"✏️ Чтобы ответить — жми «Ответить» на это сообщение"
        f" и напиши текст."
    )

    pending_questions[forwarded.message_id] = user_id

    await message.answer(
        "✅ Твой вопрос отправлен! Мы ответим в ближайшее время."
    )
    await state.clear()


@contact_router.message(Command("cancel"))
async def contact_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отправка вопроса отменена.")


@contact_router.message(lambda msg: msg.reply_to_message is not None)
async def admin_reply(message: types.Message):

    if message.chat.id != ADMIN_GROUP_ID:
        return

    original_msg_id = message.reply_to_message.message_id
    user_id = pending_questions.get(original_msg_id)

    if user_id is None:
        return

    try:
        await message.bot.send_message(
            user_id,
            f"📩 Ответ от команды UK Study Buddy:\n\n{message.text}"
        )
        await message.reply("✅ Ответ отправлен пользователю.")
    except Exception:
        await message.reply("❌ Не удалось отправить ответ.")
import json
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.main_menu import get_main_keyboard
from database import get_db

start_router = Router()


class SearchStates(StatesGroup):
    waiting_for_age = State()
    waiting_for_city = State()
    waiting_for_duration = State()
    waiting_for_sort = State()


def map_duration(duration: str) -> str:
    mapping = {
        "short": "Краткосрочный",
        "medium": "Среднесрочный",
        "long": "Долгосрочный",
    }
    return mapping.get(duration, "")


async def delete_last_bot_message(bot, chat_id: int, message_id: int):
    if message_id:
        try:
            await bot.delete_message(chat_id, message_id)
        except Exception:
            pass


async def delete_instruction(state: FSMContext, bot, chat_id: int):
    data = await state.get_data()
    msg_id = data.get("contact_instruction_id")
    if msg_id:
        await delete_last_bot_message(bot, chat_id, msg_id)
        await state.update_data(contact_instruction_id=None)


async def delete_menu_prompt(state: FSMContext, bot, chat_id: int):
    """Удаляет сообщение 'Выбери, что хочешь сделать', если оно есть."""
    data = await state.get_data()
    msg_id = data.get("menu_prompt_id")
    if msg_id:
        await delete_last_bot_message(bot, chat_id, msg_id)
        await state.update_data(menu_prompt_id=None)


async def get_filtered_schools(age: str, city: str, duration: str, sort_type: str) -> list:
    db = await get_db()
    try:
        query = "SELECT * FROM schools WHERE 1=1"
        params = []

        if age and age != "age_all":
            age_map = {"age_adults": "👨 Взрослым", "age_kids": "🧒 Детям"}
            query += " AND age_group = ?"
            params.append(age_map.get(age, age))

        if city and city != "city_all":
            city_map = {"city_london": "Лондон"}
            query += " AND city = ?"
            params.append(city_map.get(city, city))

        if sort_type == "cheap":
            query += " ORDER BY price_per_week ASC"
        elif sort_type == "expensive":
            query += " ORDER BY price_per_week DESC"
        elif sort_type == "rating":
            query += " ORDER BY rating DESC"

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()

        schools = []
        mapped_duration = map_duration(duration) if duration else ""
        for row in rows:
            school = dict(row)
            if mapped_duration:
                durations_list = json.loads(school["durations"])
                if mapped_duration not in durations_list:
                    continue
            schools.append(school)

        return schools
    finally:
        await db.close()


# --- Кнопки "Назад" ---

@start_router.callback_query(F.data == "back_to_menu")
async def cb_back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    await delete_instruction(state, callback.bot, callback.message.chat.id)
    data = await state.get_data()
    await delete_last_bot_message(callback.bot, callback.message.chat.id, data.get("step_msg_id"))
    await state.clear()
    sent = await callback.message.answer(
        "Выбери, что хочешь сделать 👇",
        reply_markup=get_main_keyboard()
    )
    await state.update_data(menu_prompt_id=sent.message_id)
    await callback.answer()


@start_router.callback_query(F.data == "back_to_age")
async def cb_back_to_age(callback: types.CallbackQuery, state: FSMContext):
    await delete_instruction(state, callback.bot, callback.message.chat.id)
    data = await state.get_data()
    await delete_last_bot_message(callback.bot, callback.message.chat.id, data.get("step_msg_id"))
    await state.set_state(SearchStates.waiting_for_city)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👨 Взрослым", callback_data="age_adults")],
            [InlineKeyboardButton(text="🧒 Детям", callback_data="age_kids")],
            [InlineKeyboardButton(text="🌍 Неважно", callback_data="age_all")],
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_to_menu")],
        ]
    )
    sent = await callback.message.answer("🔍 Для кого ищешь школу английского? 👇", reply_markup=keyboard)
    await state.update_data(step_msg_id=sent.message_id)
    await callback.answer()


@start_router.callback_query(F.data == "back_to_city")
async def cb_back_to_city(callback: types.CallbackQuery, state: FSMContext):
    await delete_instruction(state, callback.bot, callback.message.chat.id)
    data = await state.get_data()
    await delete_last_bot_message(callback.bot, callback.message.chat.id, data.get("step_msg_id"))
    await state.set_state(SearchStates.waiting_for_duration)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏛 Лондон", callback_data="city_london")],
            [InlineKeyboardButton(text="🤷 Не важно", callback_data="city_all")],
            [InlineKeyboardButton(text="← Назад", callback_data="back_to_age")],
        ]
    )
    sent = await callback.message.answer("🏙 Выбери город.", reply_markup=keyboard)
    await state.update_data(step_msg_id=sent.message_id)
    await callback.answer()


@start_router.callback_query(F.data == "back_to_duration")
async def cb_back_to_duration(callback: types.CallbackQuery, state: FSMContext):
    await delete_instruction(state, callback.bot, callback.message.chat.id)
    data = await state.get_data()
    await delete_last_bot_message(callback.bot, callback.message.chat.id, data.get("step_msg_id"))
    await state.set_state(SearchStates.waiting_for_sort)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟢 Краткосрочный (1-4 нед)", callback_data="dur_short")],
            [InlineKeyboardButton(text="🟡 Среднесрочный (1-6 мес)", callback_data="dur_medium")],
            [InlineKeyboardButton(text="🔴 Долгосрочный (6-12+ мес)", callback_data="dur_long")],
            [InlineKeyboardButton(text="← Назад", callback_data="back_to_city")],
        ]
    )
    sent = await callback.message.answer("⏳ Длительность?", reply_markup=keyboard)
    await state.update_data(step_msg_id=sent.message_id)
    await callback.answer()


# --- Основные обработчики ---

@start_router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()

    if message.from_user:
        db = await get_db()
        try:
            user = await db.execute("SELECT id FROM users WHERE id = ?", (message.from_user.id,))
            row = await user.fetchone()
            if row is None:
                await db.execute(
                    "INSERT INTO users (id, username, first_name, last_name, is_subscribed) VALUES (?, ?, ?, ?, 1)",
                    (message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name),
                )
                await db.commit()
            else:
                await db.execute(
                    "UPDATE users SET username = ?, first_name = ?, last_name = ? WHERE id = ?",
                    (message.from_user.username, message.from_user.first_name, message.from_user.last_name, message.from_user.id),
                )
                await db.commit()
        finally:
            await db.close()

    name = message.from_user.first_name if message.from_user and message.from_user.first_name else "Студент"

    try:
        await message.answer(
            f"Привет, {name}! 👋\n\n"
            f"Я помогу найти школу английского в Великобритании.\n"
            f"Выбери, что хочешь сделать 👇",
            reply_markup=get_main_keyboard()
        )
    except Exception:
        pass


@start_router.callback_query(F.data == "search")
async def cb_search(callback: types.CallbackQuery, state: FSMContext):
    await delete_instruction(state, callback.bot, callback.message.chat.id)
    await delete_menu_prompt(state, callback.bot, callback.message.chat.id)
    data = await state.get_data()
    await delete_last_bot_message(callback.bot, callback.message.chat.id, data.get("step_msg_id"))
    await state.clear()
    await state.set_state(SearchStates.waiting_for_city)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👨 Взрослым", callback_data="age_adults")],
            [InlineKeyboardButton(text="🧒 Детям", callback_data="age_kids")],
            [InlineKeyboardButton(text="🌍 Неважно", callback_data="age_all")],
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_to_menu")],
        ]
    )
    sent = await callback.message.answer("🔍 Для кого ищешь школу английского? 👇", reply_markup=keyboard)
    await state.update_data(step_msg_id=sent.message_id)
    await callback.answer()


@start_router.callback_query(F.data.in_(["age_adults", "age_kids", "age_all"]))
async def cb_age(callback: types.CallbackQuery, state: FSMContext):
    await delete_instruction(state, callback.bot, callback.message.chat.id)
    data = await state.get_data()
    await delete_last_bot_message(callback.bot, callback.message.chat.id, data.get("step_msg_id"))
    await state.update_data(age=callback.data)
    await state.set_state(SearchStates.waiting_for_duration)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏛 Лондон", callback_data="city_london")],
            [InlineKeyboardButton(text="🤷 Не важно", callback_data="city_all")],
            [InlineKeyboardButton(text="← Назад", callback_data="back_to_age")],
        ]
    )
    sent = await callback.message.answer("🏙 Выбери город.", reply_markup=keyboard)
    await state.update_data(step_msg_id=sent.message_id)
    await callback.answer()


@start_router.callback_query(F.data.in_(["city_london", "city_all"]))
async def cb_city(callback: types.CallbackQuery, state: FSMContext):
    await delete_instruction(state, callback.bot, callback.message.chat.id)
    data = await state.get_data()
    await delete_last_bot_message(callback.bot, callback.message.chat.id, data.get("step_msg_id"))
    await state.update_data(city=callback.data)
    await state.set_state(SearchStates.waiting_for_sort)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟢 Краткосрочный (1-4 нед)", callback_data="dur_short")],
            [InlineKeyboardButton(text="🟡 Среднесрочный (1-6 мес)", callback_data="dur_medium")],
            [InlineKeyboardButton(text="🔴 Долгосрочный (6-12+ мес)", callback_data="dur_long")],
            [InlineKeyboardButton(text="← Назад", callback_data="back_to_city")],
        ]
    )
    sent = await callback.message.answer("⏳ Длительность?", reply_markup=keyboard)
    await state.update_data(step_msg_id=sent.message_id)
    await callback.answer()


@start_router.callback_query(F.data.in_(["dur_short", "dur_medium", "dur_long"]))
async def cb_duration(callback: types.CallbackQuery, state: FSMContext):
    await delete_instruction(state, callback.bot, callback.message.chat.id)
    data = await state.get_data()
    await delete_last_bot_message(callback.bot, callback.message.chat.id, data.get("step_msg_id"))
    await state.update_data(duration=callback.data.replace("dur_", ""))
    await state.set_state(SearchStates.waiting_for_sort)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💰 Дешевле", callback_data="sort_cheap")],
            [InlineKeyboardButton(text="💎 Дороже", callback_data="sort_expensive")],
            [InlineKeyboardButton(text="⭐ По рейтингу", callback_data="sort_rating")],
            [InlineKeyboardButton(text="← Назад", callback_data="back_to_duration")],
        ]
    )
    sent = await callback.message.answer("📊 Как отсортировать?", reply_markup=keyboard)
    await state.update_data(step_msg_id=sent.message_id)
    await callback.answer()


@start_router.callback_query(F.data.in_(["sort_cheap", "sort_expensive", "sort_rating"]))
async def cb_sort(callback: types.CallbackQuery, state: FSMContext):
    await delete_instruction(state, callback.bot, callback.message.chat.id)
    data = await state.get_data()
    age = data.get("age", "age_all")
    city = data.get("city", "city_all")
    duration = data.get("duration", "")
    sort_type = callback.data.replace("sort_", "")

    schools = await get_filtered_schools(age, city, duration, sort_type)

    await delete_last_bot_message(callback.bot, callback.message.chat.id, data.get("step_msg_id"))

    if not schools:
        await callback.message.answer(
            "😕 Ничего не найдено.\n\nНажми /start чтобы попробовать снова.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        await callback.answer()
        return

    text = f"🔍 Нашёл {len(schools)} школ:\n\n"
    for i, school in enumerate(schools, 1):
        durations_list = json.loads(school["durations"])
        durations_text = ", ".join(durations_list)
        text += f"{i}. 🏫 {school['name']}\n   📍 {school['city']}\n   💰 £{school['price_per_week']}/нед\n   ⭐ {school['rating']}/5\n   📆 {durations_text}\n   📝 {school['description']}\n\n"

    await callback.message.answer(text, reply_markup=get_main_keyboard())
    await state.clear()
    await callback.answer()


@start_router.callback_query(F.data == "contact")
async def cb_contact(callback: types.CallbackQuery, state: FSMContext):
    await delete_instruction(state, callback.bot, callback.message.chat.id)
    await delete_menu_prompt(state, callback.bot, callback.message.chat.id)
    data = await state.get_data()
    await delete_last_bot_message(callback.bot, callback.message.chat.id, data.get("step_msg_id"))
    await state.clear()
    sent = await callback.message.answer(
        "📩 Напиши свой вопрос прямо в чат — я перешлю его команде.\n\nДля отмены нажми /cancel",
        reply_markup=get_main_keyboard()
    )
    await state.update_data(contact_instruction_id=sent.message_id)
    await callback.answer()
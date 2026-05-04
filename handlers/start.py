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
    waiting_for_favorite = State()


def map_duration(duration: str) -> str:
    mapping = {
        "short": "Краткосрочный",
        "medium": "Среднесрочный",
        "long": "Долгосрочный",
    }
    return mapping.get(duration, "")


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

    await message.answer(
        f"Привет, {name}! 👋\n\n"
        f"Я помогу найти школу английского в Великобритании.\n"
        f"Выбери, что хочешь сделать 👇",
        reply_markup=get_main_keyboard()
    )


# --- CALLBACK-ОБРАБОТЧИКИ ---

@start_router.callback_query(F.data == "search")
async def cb_search(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👨 Взрослым", callback_data="age_adults")],
            [InlineKeyboardButton(text="🧒 Детям", callback_data="age_kids")],
            [InlineKeyboardButton(text="🌍 Неважно", callback_data="age_all")],
        ]
    )
    await callback.message.edit_text("🔍 Для кого ищешь школу английского? 👇", reply_markup=keyboard)
    await callback.answer()


@start_router.callback_query(F.data.in_(["age_adults", "age_kids", "age_all"]))
async def cb_age(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(age=callback.data)
    await state.set_state(SearchStates.waiting_for_city)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏛 Лондон", callback_data="city_london")],
            [InlineKeyboardButton(text="🤷 Не важно", callback_data="city_all")],
        ]
    )
    await callback.message.edit_text("🏙 Выбери город.", reply_markup=keyboard)
    await callback.answer()


@start_router.callback_query(F.data.in_(["city_london", "city_all"]))
async def cb_city(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(city=callback.data)
    await state.set_state(SearchStates.waiting_for_duration)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟢 Краткосрочный (1-4 нед)", callback_data="dur_short")],
            [InlineKeyboardButton(text="🟡 Среднесрочный (1-6 мес)", callback_data="dur_medium")],
            [InlineKeyboardButton(text="🔴 Долгосрочный (6-12+ мес)", callback_data="dur_long")],
        ]
    )
    await callback.message.edit_text("⏳ Длительность?", reply_markup=keyboard)
    await callback.answer()


@start_router.callback_query(F.data.in_(["dur_short", "dur_medium", "dur_long"]))
async def cb_duration(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(duration=callback.data.replace("dur_", ""))
    await state.set_state(SearchStates.waiting_for_sort)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💰 Дешевле", callback_data="sort_cheap")],
            [InlineKeyboardButton(text="💎 Дороже", callback_data="sort_expensive")],
            [InlineKeyboardButton(text="⭐ По рейтингу", callback_data="sort_rating")],
        ]
    )
    await callback.message.edit_text("📊 Как отсортировать?", reply_markup=keyboard)
    await callback.answer()


@start_router.callback_query(F.data.in_(["sort_cheap", "sort_expensive", "sort_rating"]))
async def cb_sort(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    age = data.get("age", "age_all")
    city = data.get("city", "city_all")
    duration = data.get("duration", "")
    sort_type = callback.data.replace("sort_", "")

    schools = await get_filtered_schools(age, city, duration, sort_type)

    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO search_history (user_id, age, city, duration, sort_type, results_count) VALUES (?, ?, ?, ?, ?, ?)",
            (callback.from_user.id, age, city, duration, sort_type, len(schools) if schools else 0),
        )
        await db.commit()
    finally:
        await db.close()

    if not schools:
        await callback.message.edit_text(
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

    text += "⭐ Чтобы добавить в избранное — напиши номер."

    await callback.message.edit_text(text, reply_markup=get_main_keyboard())
    await state.set_state(SearchStates.waiting_for_favorite)
    await callback.answer()


# --- КНОПКИ МЕНЮ ---

@start_router.callback_query(F.data == "schools")
async def cb_schools(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM schools")
        schools = await cursor.fetchall()
    finally:
        await db.close()

    if not schools:
        await callback.message.edit_text("🏫 Пока нет доступных школ.", reply_markup=get_main_keyboard())
        await callback.answer()
        return

    text = "🏫 Наши школы:\n\n"
    for school in schools:
        school = dict(school)
        durations_list = json.loads(school["durations"])
        durations_text = ", ".join(durations_list)
        text += f"🏫 {school['name']}\n   📍 {school['city']}\n   💰 £{school['price_per_week']}/нед\n   ⭐ {school['rating']}/5\n   📆 {durations_text}\n   📝 {school['description']}\n\n"

    await callback.message.edit_text(text, reply_markup=get_main_keyboard())
    await callback.answer()


@start_router.callback_query(F.data == "discounts")
async def cb_discounts(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "💰 Акции и скидки от языковых школ.\n\nЗдесь будут появляться горящие предложения и специальные цены.\n\n🔔 Нажми /subscribe для уведомлений.",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


@start_router.callback_query(F.data == "favorites")
async def cb_favorites(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not callback.from_user:
        await callback.answer()
        return

    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT s.name, s.city, s.price_per_week, s.rating FROM favorites f JOIN schools s ON f.school_id = s.id WHERE f.user_id = ?",
            (callback.from_user.id,),
        )
        favorites = await cursor.fetchall()
    finally:
        await db.close()

    if not favorites:
        await callback.message.edit_text(
            "⭐ У тебя пока нет избранных школ.\n\nНажми «🔍 Подобрать курс», чтобы найти школу.",
            reply_markup=get_main_keyboard()
        )
        await callback.answer()
        return

    text = "⭐ Твои избранные школы:\n\n"
    for i, fav in enumerate(favorites, 1):
        fav = dict(fav)
        text += f"{i}. 🏫 {fav['name']}\n   📍 {fav['city']}\n   💰 £{fav['price_per_week']}/нед\n   ⭐ {fav['rating']}/5\n\n"

    await callback.message.edit_text(text, reply_markup=get_main_keyboard())
    await callback.answer()


@start_router.callback_query(F.data == "contact")
async def cb_contact(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "📩 Напиши свой вопрос прямо в чат — я перешлю его команде.\n\nДля отмены нажми /cancel",
        reply_markup=get_main_keyboard()
    )
    await state.set_state(SearchStates.waiting_for_favorite)
    await callback.answer()


# --- ДОБАВЛЕНИЕ В ИЗБРАННОЕ ПО НОМЕРУ ---

@start_router.message(SearchStates.waiting_for_favorite)
async def handle_favorite_by_number(message: types.Message, state: FSMContext):
    if not message.from_user or not message.text:
        return

    if message.text in ["/start", "/subscribe", "/unsubscribe", "/cancel"]:
        await state.clear()
        return

    try:
        index = int(message.text.strip()) - 1
    except ValueError:
        return

    if index < 0:
        await message.answer("Номер должен быть положительным.")
        return

    data = await state.get_data()
    schools = await get_filtered_schools(
        data.get("age", "age_all"),
        data.get("city", "city_all"),
        data.get("duration", ""),
        data.get("sort_type", "")
    )

    if index >= len(schools):
        await message.answer(f"В списке всего {len(schools)} школ. Введи номер от 1 до {len(schools)}.")
        return

    school = schools[index]
    db = await get_db()
    try:
        row = await db.execute("SELECT id FROM favorites WHERE user_id = ? AND school_id = ?", (message.from_user.id, school["id"]))
        existing = await row.fetchone()
        if existing:
            await message.answer(f"⭐ {school['name']} уже в избранном!")
        else:
            await db.execute("INSERT INTO favorites (user_id, school_id) VALUES (?, ?)", (message.from_user.id, school["id"]))
            await db.commit()
            await message.answer(f"⭐ {school['name']} добавлена в избранное!")
    finally:
        await db.close()
    await state.clear()
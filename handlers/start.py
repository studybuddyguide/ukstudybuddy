import json
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from keyboards.main_menu import get_main_keyboard
from database import async_session
from models import User, School, SearchHistory, Favorite

start_router = Router()


class SearchStates(StatesGroup):
    waiting_for_age = State()
    waiting_for_city = State()
    waiting_for_duration = State()
    waiting_for_sort = State()
    waiting_for_favorite = State()


def map_duration(duration: str) -> str:
    mapping = {
        "🟢 Краткосрочный (1–4 нед)": "Краткосрочный",
        "🟡 Среднесрочный (1–6 мес)": "Среднесрочный",
        "🔴 Долгосрочный (6–12+ мес)": "Долгосрочный",
    }
    return mapping.get(duration, "")


async def get_filtered_schools(age: str, city: str, duration: str, sort_type: str) -> list:
    async with async_session() as session:
        result = await session.execute(select(School))
        schools = list(result.scalars().all())

    if age and age != "🌍 Неважно (все курсы)":
        schools = [s for s in schools if s.age_group == age]

    if city and city != "🤷 Не важно":
        city_name = city.replace("🏛 ", "")
        schools = [s for s in schools if s.city == city_name]

    mapped_duration = map_duration(duration)
    if mapped_duration:
        filtered = []
        for s in schools:
            durations_list = json.loads(s.durations)
            if mapped_duration in durations_list:
                filtered.append(s)
        schools = filtered

    if sort_type == "💰 Дешевле":
        schools.sort(key=lambda s: s.price_per_week)
    elif sort_type == "💎 Дороже":
        schools.sort(key=lambda s: s.price_per_week, reverse=True)
    elif sort_type == "⭐ По рейтингу":
        schools.sort(key=lambda s: s.rating, reverse=True)

    return schools


@start_router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()

    if message.from_user:
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
                await session.commit()
            else:
                user.username = message.from_user.username
                user.first_name = message.from_user.first_name
                user.last_name = message.from_user.last_name
                await session.commit()

    if message.from_user and message.from_user.first_name:
        name = message.from_user.first_name
    else:
        name = "Студент"

    await message.answer(
        f"Привет, {name}! 👋\n\n"
        f"Я помогу найти школу английского в Великобритании.\n"
        f"Выбери, что хочешь сделать 👇",
        reply_markup=get_main_keyboard()
    )


@start_router.message(lambda msg: msg.text == "🔍 Подобрать курс")
async def button_search(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👨 Взрослым")],
            [KeyboardButton(text="🧒 Детям")],
            [KeyboardButton(text="🌍 Неважно (все курсы)")],
        ],
        resize_keyboard=True
    )
    await message.answer(
        "🔍 Отлично! Давай подберём тебе курс.\n\n"
        "Для кого ищешь школу английского? 👇",
        reply_markup=keyboard
    )


@start_router.message(lambda msg: msg.text in ["👨 Взрослым", "🧒 Детям", "🌍 Неважно (все курсы)"])
async def process_age_choice(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(SearchStates.waiting_for_city)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏛 Лондон")],
            [KeyboardButton(text="🤷 Не важно")],
        ],
        resize_keyboard=True
    )
    await message.answer(
        "🏙 Отлично! Теперь выбери город, где хочешь учиться.\n\n"
        "Если не знаешь или хочешь посмотреть все варианты — "
        "нажми «Не важно».",
        reply_markup=keyboard
    )


@start_router.message(lambda msg: msg.text in ["🏛 Лондон", "🤷 Не важно"])
async def process_city_choice(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(SearchStates.waiting_for_duration)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🟢 Краткосрочный (1–4 нед)")],
            [KeyboardButton(text="🟡 Среднесрочный (1–6 мес)")],
            [KeyboardButton(text="🔴 Долгосрочный (6–12+ мес)")],
        ],
        resize_keyboard=True
    )
    await message.answer(
        "⏳ Сколько времени готов уделить учёбе?\n\n"
        "🟢 Краткосрочный — каникулы, интенсивы\n"
        "🟡 Среднесрочный — семестр, подготовка к IELTS\n"
        "🔴 Долгосрочный — академический год, полное погружение",
        reply_markup=keyboard
    )


@start_router.message(lambda msg: msg.text in [
    "🟢 Краткосрочный (1–4 нед)",
    "🟡 Среднесрочный (1–6 мес)",
    "🔴 Долгосрочный (6–12+ мес)"
])
async def process_duration_choice(message: types.Message, state: FSMContext):
    await state.update_data(duration=message.text)
    await state.set_state(SearchStates.waiting_for_sort)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Дешевле")],
            [KeyboardButton(text="💎 Дороже")],
            [KeyboardButton(text="⭐ По рейтингу")],
        ],
        resize_keyboard=True
    )
    await message.answer(
        "📊 Отлично! Я подобрал для тебя школы.\n\n"
        "Как хочешь отсортировать результаты? 👇",
        reply_markup=keyboard
    )


@start_router.message(lambda msg: msg.text in ["💰 Дешевле", "💎 Дороже", "⭐ По рейтингу"])
async def process_sort_choice(message: types.Message, state: FSMContext):
    data = await state.get_data()
    age = data.get("age", "")
    city = data.get("city", "")
    duration = data.get("duration", "")
    sort_type = message.text

    await state.update_data(sort_type=sort_type)

    schools = await get_filtered_schools(age, city, duration, sort_type)

    async with async_session() as session:
        history = SearchHistory(
            user_id=message.from_user.id,
            age=age,
            city=city,
            duration=duration,
            sort_type=sort_type,
            results_count=len(schools) if schools else 0,
        )
        session.add(history)
        await session.commit()

    if not schools:
        await message.answer(
            "😕 К сожалению, по твоим критериям ничего не найдено.\n\n"
            "Попробуй изменить параметры — нажми «🔍 Подобрать курс» ещё раз.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        return

    text = f"🔍 Нашёл {len(schools)} школ:\n\n"
    for i, school in enumerate(schools, 1):
        durations_list = json.loads(school.durations)
        durations_text = ", ".join(durations_list)
        text += (
            f"{i}. 🏫 {school.name}\n"
            f"   📍 {school.city}\n"
            f"   💰 £{school.price_per_week}/нед\n"
            f"   ⭐ {school.rating}/5\n"
            f"   📆 {durations_text}\n"
            f"   📝 {school.description}\n\n"
        )

    text += "⭐ Чтобы добавить школу в избранное — напиши её номер."

    await message.answer(text, reply_markup=get_main_keyboard())
    await state.set_state(SearchStates.waiting_for_favorite)


@start_router.message(SearchStates.waiting_for_favorite)
async def add_to_favorites_by_number(message: types.Message, state: FSMContext):
    if not message.from_user or not message.text:
        return

    try:
        index = int(message.text.strip()) - 1
    except ValueError:
        return

    if index < 0:
        await message.answer("Номер должен быть положительным. Попробуй ещё раз.")
        return

    data = await state.get_data()
    age = data.get("age", "")
    city = data.get("city", "")
    duration = data.get("duration", "")
    sort_type = data.get("sort_type", "")

    schools = await get_filtered_schools(age, city, duration, sort_type)

    if index >= len(schools):
        await message.answer(
            f"В списке всего {len(schools)} школ. Введи номер от 1 до {len(schools)}."
        )
        return

    school = schools[index]

    async with async_session() as session:
        result = await session.execute(
            select(Favorite).where(
                Favorite.user_id == message.from_user.id,
                Favorite.school_id == school.id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            await message.answer(f"⭐ {school.name} уже в избранном!")
        else:
            fav = Favorite(user_id=message.from_user.id, school_id=school.id)
            session.add(fav)
            await session.commit()
            await message.answer(f"⭐ {school.name} добавлена в избранное!")

    await state.clear()


@start_router.message(lambda msg: msg.text == "🏫 Наши школы")
async def button_schools(message: types.Message, state: FSMContext):
    await state.clear()

    async with async_session() as session:
        result = await session.execute(select(School))
        schools = list(result.scalars().all())

    if not schools:
        await message.answer("🏫 Пока нет доступных школ.")
        return

    text = "🏫 Наши школы:\n\n"
    for school in schools:
        durations_list = json.loads(school.durations)
        durations_text = ", ".join(durations_list)
        text += (
            f"🏫 {school.name}\n"
            f"   📍 {school.city}\n"
            f"   💰 £{school.price_per_week}/нед\n"
            f"   ⭐ {school.rating}/5\n"
            f"   📆 {durations_text}\n"
            f"   📝 {school.description}\n\n"
        )

    await message.answer(text)


@start_router.message(lambda msg: msg.text == "💰 Скидки")
async def button_discounts(message: types.Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "💰 Акции и скидки от языковых школ.\n\n"
        "Здесь будут появляться горящие предложения и специальные цены. "
        "Заглядывай почаще!\n\n"
        "🔔 Хочешь получать уведомления о новых скидках? "
        "Нажми /subscribe"
    )
from aiogram import Router, types
from aiogram.filters import Command

from keyboards.main_menu import get_main_keyboard

start_router = Router()


@start_router.message(Command("start"))
async def cmd_start(message: types.Message):
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
    await message.answer(
        "🔍 Этот раздел скоро заработает в полную силу. Следи за обновлениями!"
    )


@start_router.message(lambda msg: msg.text == "🏫 Наши школы")
async def button_schools(message: types.Message):
    await message.answer(
        "🏫 Скоро здесь появится список школ с подробным описанием, "
        "ценами и отзывами. Следи за обновлениями!"
    )


@start_router.message(lambda msg: msg.text == "💰 Скидки")
async def button_discounts(message: types.Message):
    await message.answer(
        "💰 Здесь будут появляться горящие предложения и специальные цены. "
        "Заглядывай почаще!"
    )


@start_router.message(lambda msg: msg.text == "📩 Связаться с нами")
async def button_contact(message: types.Message):
    await message.answer(
        "📩 Есть вопросы или нужна помощь с выбором?\n\n"
        "Напиши нам в Telegram: @your_username\n"
        "Или на почту: hello@ukstudybuddy.com\n\n"
        "Ответим в течение 24 часов!"
    )

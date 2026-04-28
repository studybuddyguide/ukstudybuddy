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
        f"Привет, {name}! Нажми на кнопку ниже 👇",
        reply_markup=get_main_keyboard()
    )


@start_router.message(lambda msg: msg.text == "👋 Поздороваться")
async def button_hello(message: types.Message):
    if message.from_user and message.from_user.first_name:
        name = message.from_user.first_name
    else:
        name = "Студент"
    await message.answer(f"Привет, {name}!")

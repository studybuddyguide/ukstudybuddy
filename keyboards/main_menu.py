from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Подобрать курс")],
            [
                KeyboardButton(text="🏫 Наши школы"),
                KeyboardButton(text="💰 Скидки"),
            ],
            [KeyboardButton(text="📩 Связаться с нами")],
        ],
        resize_keyboard=True
    )
    return keyboard

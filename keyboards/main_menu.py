from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👋 Поздороваться")]
        ],
        resize_keyboard=True
    )

    return keyboard

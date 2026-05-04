from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Подобрать курс", callback_data="search")],
            [InlineKeyboardButton(text="📩 Связаться с нами", callback_data="contact")],
        ]
    )
    return keyboard
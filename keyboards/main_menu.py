from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Подобрать курс", callback_data="search")],
            [
                InlineKeyboardButton(text="🏫 Наши школы", callback_data="schools"),
                InlineKeyboardButton(text="💰 Скидки", callback_data="discounts"),
            ],
            [
                InlineKeyboardButton(text="⭐ Избранное", callback_data="favorites"),
                InlineKeyboardButton(text="📩 Связаться с нами", callback_data="contact"),
            ],
        ]
    )
    return keyboard
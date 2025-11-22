from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

start = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎒 Начать тур", callback_data="start_tour")]
])

restart = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Обратная связь ✍🏼", url="https://vk.com")],
    [InlineKeyboardButton(text="Таблица лидеров 🏆", callback_data="table_lider")]
])
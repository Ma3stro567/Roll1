from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text

import logging

# Настройка логгирования
logging.basicConfig(level=logging.INFO)

# Ваш токен бота
BOT_TOKEN = "8152843550:AAH2ty2PVrJ3_gDllmE9sNn9r4XkveDTK_k"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Словарь для хранения данных пользователей
users_data = {}

# Минимальные ограничения
MIN_BET = 0.05
MIN_TOP_UP = 0.05
MIN_WITHDRAW = 0.05

# Основная клавиатура
main_menu_kb = InlineKeyboardMarkup(row_width=1)
main_menu_kb.add(
    InlineKeyboardButton("🎮 Играть", callback_data="play"),
    InlineKeyboardButton("👤 Профиль", callback_data="profile"),
)

# Клавиатура профиля
profile_kb = InlineKeyboardMarkup(row_width=2)
profile_kb.add(
    InlineKeyboardButton("➕ Пополнить", callback_data="top_up"),
    InlineKeyboardButton("➖ Вывести", callback_data="withdraw"),
    InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
)

# Обработка команды /start
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    user_id = message.from_user.id

    # Инициализация данных пользователя
    if user_id not in users_data:
        users_data[user_id] = {"balance": 0.0}

    await message.answer(
        "🎉 Добро пожаловать в бота! 🎉\nВыберите действие ниже:",
        reply_markup=main_menu_kb
    )

# Обработка нажатия кнопки "Играть"
@dp.callback_query_handler(Text(equals="play"))
async def play_game(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    if users_data[user_id]["balance"] < MIN_BET:
        await callback_query.message.edit_text(
            f"❌ У вас недостаточно средств для игры! Минимальная ставка: {MIN_BET} USDT.",
            reply_markup=main_menu_kb
        )
        return

    # Вычитаем ставку и рассчитываем выигрыш
    users_data[user_id]["balance"] -= MIN_BET
    if True:  # Здесь можете вставить свою логику выигрыша
        win_amount = MIN_BET * 1.80
        users_data[user_id]["balance"] += win_amount
        await callback_query.message.edit_text(
            f"🎉 Вы выиграли {win_amount:.2f} USDT! Ваш баланс: {users_data[user_id]['balance']:.2f} USDT.",
            reply_markup=main_menu_kb
        )
    else:
        await callback_query.message.edit_text(
            f"😢 Вы проиграли! Ваш баланс: {users_data[user_id]['balance']:.2f} USDT.",
            reply_markup=main_menu_kb
        )

# Обработка нажатия кнопки "Профиль"
@dp.callback_query_handler(Text(equals="profile"))
async def profile(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    balance = users_data[user_id]["balance"]

    await callback_query.message.edit_text(
        f"👤 Ваш профиль:\n💰 Баланс: {balance:.2f} USDT",
        reply_markup=profile_kb
    )

# Обработка кнопки "Пополнить"
@dp.callback_query_handler(Text(equals="top_up"))
async def top_up(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text(
        f"➕ Минимальное пополнение: {MIN_TOP_UP} USDT. Введите сумму пополнения:"
    )

@dp.message_handler(lambda message: message.text.isdigit())
async def handle_top_up(message: types.Message):
    user_id = message.from_user.id
    amount = float(message.text)

    if amount < MIN_TOP_UP:
        await message.answer(f"❌ Сумма пополнения должна быть не менее {MIN_TOP_UP} USDT.")
        return

    users_data[user_id]["balance"] += amount
    await message.answer(f"✅ Ваш баланс успешно пополнен на {amount:.2f} USDT. Текущий баланс: {users_data[user_id]['balance']:.2f} USDT.")

# Обработка кнопки "Вывести"
@dp.callback_query_handler(Text(equals="withdraw"))
async def withdraw(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text(
        f"➖ Минимальный вывод: {MIN_WITHDRAW} USDT. Введите сумму вывода:"
    )

@dp.message_handler(lambda message: message.text.isdigit())
async def handle_withdraw(message: types.Message):
    user_id = message.from_user.id
    amount = float(message.text)

    if amount < MIN_WITHDRAW:
        await message.answer(f"❌ Сумма вывода должна быть не менее {MIN_WITHDRAW} USDT.")
        return

    if amount > users_data[user_id]["balance"]:
        await message.answer("❌ Недостаточно средств на балансе.")
        return

    users_data[user_id]["balance"] -= amount
    await message.answer(f"✅ Вы успешно вывели {amount:.2f} USDT. Текущий баланс: {users_data[user_id]['balance']:.2f} USDT.")

# Обработка кнопки "Назад"
@dp.callback_query_handler(Text(equals="back_to_main"))
async def back_to_main(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text(
        "⬅️ Вы вернулись в главное меню:",
        reply_markup=main_menu_kb
    )

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

import os
import random
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# Укажите ваш токен бота
API_TOKEN = "ВАШ_ТОКЕН"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Словарь для хранения балансов пользователей
user_balances = {}


# Функция для создания кнопок профиля
def get_profile_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Пополнить", callback_data="deposit"),
        InlineKeyboardButton("Вывести", callback_data="withdraw")
    )
    return keyboard


# Команда /start
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    user_id = message.from_user.id
    # Инициализация баланса пользователя
    if user_id not in user_balances:
        user_balances[user_id] = 0.0
    await message.answer(
        f"Добро пожаловать, {message.from_user.first_name}!\n"
        f"Ваш баланс: {user_balances[user_id]:.2f} USDT.\n"
        "Чтобы посмотреть профиль, нажмите на кнопку ниже.",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("Открыть профиль", callback_data="profile")
        ),
    )


# Обработка инлайн-кнопок
@dp.callback_query_handler(lambda call: True)
async def callback_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    # Профиль пользователя
    if callback_query.data == "profile":
        balance = user_balances.get(user_id, 0.0)
        await bot.send_message(
            user_id,
            f"Ваш профиль:\nБаланс: {balance:.2f} USDT",
            reply_markup=get_profile_keyboard(),
        )

    # Пополнение баланса
    elif callback_query.data == "deposit":
        await bot.send_message(user_id, "Введите сумму для пополнения (например, 10):")
        # Сохраняем состояние для обработки суммы
        dp.register_message_handler(process_deposit, state=None)

    # 
    

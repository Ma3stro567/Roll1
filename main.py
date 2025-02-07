from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import random

API_TOKEN = '8152843550:AAH2ty2PVrJ3_gDllmE9sNn9r4XkveDTK_k'

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Словарь для хранения данных пользователей
user_data = {}

# Главное меню
def main_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🎲 Играть", callback_data="play_game"))
    keyboard.add(InlineKeyboardButton("💰 Сделать ставку", callback_data="set_bet"))
    return keyboard

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"balance": 10.0, "bet": 0.05}  # Начальный баланс и минимальная ставка
    await message.answer(f"👋 Привет, {message.from_user.first_name}!\n"
                         f"Ваш баланс: {user_data[user_id]['balance']} USDT\n"
                         f"Минимальная ставка: 0.05 USDT", reply_markup=main_menu())

# Обработчик кнопок
@dp.callback_query_handler()
async def callback_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data

    if data == "play_game":
        await callback_query.message.answer("🎲 Напишите в чат число от 1 до 6, чтобы сыграть!")
    elif data == "set_bet":
        await callback_query.message.answer("💰 Напишите сумму вашей ставки в формате: 0.05, 1.0 и т.д.")
    await callback_query.answer()

# Обработчик текстовых сообщений для ставок и игры
@dp.message_handler()
async def handle_message(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_data:
        await message.answer("⚠️ Сначала нажмите /start.")
        return

    # Обработка ставки
    if user_data[user_id].get("waiting_for_bet"):
        try:
            bet = float(message.text)
            if bet < 0.05:
                await message.answer("⚠️ Минимальная ставка 0.05 USDT.")
                return
            if bet > user_data[user_id]["balance"]:
                await message.answer("⚠️ Недостаточно средств для ставки.")
                return
            user_data[user_id]["bet"] = bet
            user_data[user_id]["waiting_for_bet"] = False
            await message.answer(f"✅ Ваша ставка установлена: {bet} USDT.", reply_markup=main_menu())
        except ValueError:
            await message.answer("⚠️ Введите корректное число для ставки.")
        return

    # Обработка игры
    try:
        guess = int(message.text)
        if guess < 1 or guess > 6:
            await message.answer("⚠️ Введите число от 1 до 6.")
            return

        if user_data[user_id]["bet"] > user_data[user_id]["balance"]:
            await message.answer("⚠️ Недостаточно средств для игры. Пополните баланс или уменьшите ставку.")
            return

        # Бросок кубика
        roll = random.randint(1, 6)
        if guess == roll:
            winnings = user_data[user_id]["bet"] * 2
            user_data[user_id]["balance"] += winnings
            await message.answer(f"🎉 Ура! Выпало {roll}. Вы угадали и выиграли {winnings} USDT! "
                                 f"Ваш баланс: {user_data[user_id]['balance']} USDT.")
        else:
            user_data[user_id]["balance"] -= user_data[user_id]["bet"]
            await message.answer(f"😢 Выпало {roll}. Вы проиграли. Ваш баланс: {user_data[user_id]['balance']} USDT.")
    except ValueError:
        await message.answer("⚠️ Введите корректное число от 1 до 6.")

# Установка ожидания ставки
@dp.callback_query_handler(lambda c: c.data == "set_bet")
async def set_bet_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_data[user_id]["waiting_for_bet"] = True
    await bot.send_message(user_id, "💰 Напишите сумму вашей ставки.")

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
    

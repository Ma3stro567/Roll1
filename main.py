from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.middlewares.logging import LoggingMiddleware

# Укажите ваш токен бота
API_TOKEN = "8152843550:AAH2ty2PVrJ3_gDllmE9sNn9r4XkveDTK_k"

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

    # Вывод средств
    elif callback_query.data == "withdraw":
        await bot.send_message(user_id, "Введите сумму для вывода (например, 10):")
        # Сохраняем состояние для обработки суммы
        dp.register_message_handler(process_withdraw, state=None)


# Обработка пополнения
async def process_deposit(message: types.Message):
    user_id = message.from_user.id
    try:
        amount = float(message.text)
        if amount > 0:
            user_balances[user_id] += amount
            await message.answer(f"Ваш баланс успешно пополнен на {amount:.2f} USDT!")
        else:
            await message.answer("Сумма должна быть больше 0.")
    except ValueError:
        await message.answer("Введите корректную сумму (например, 10).")


# Обработка вывода
async def process_withdraw(message: types.Message):
    user_id = message.from_user.id
    try:
        amount = float(message.text)
        if amount > 0 and amount <= user_balances.get(user_id, 0.0):
            user_balances[user_id] -= amount
            await message.answer(f"Вы успешно вывели {amount:.2f} USDT!")
        else:
            await message.answer("Недостаточно средств или неверная сумма.")
    except ValueError:
        await message.answer("Введите корректную сумму (например, 10).")


# Команда для ставки
@dp.message_handler(commands=["bet"])
async def place_bet(message: types.Message):
    user_id = message.from_user.id
    try:
        # Проверка баланса
        if user_balances.get(user_id, 0.0) <= 0:
            await message.answer("Недостаточно средств для ставки.")
            return

        # Кинуть кубик
        dice = await bot.send_dice(message.chat.id)
        result = dice.dice.value

        # Выигрыш при выпадении 4, 5 или 6
        if result >= 4:
            win_amount = user_balances[user_id] * 1.80
            user_balances[user_id] = win_amount
            await message.answer(
                f"Поздравляем! Вы выиграли. Новый баланс: {win_amount:.2f} USDT."
            )
        else:
            user_balances[user_id] = 0
            await message.answer("Вы проиграли. Ваш баланс теперь 0 USDT.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")


# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

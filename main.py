import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и хранилища
bot = Bot(token='7927818935:AAEfG0GnN3dhGqG4ql3DTPj5vR29JvDVTe0')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Временное хранилище данных
users_data = {}
withdraw_requests = []
stats = {'total_users': 0, 'messages_today': 0}

# Состояния для админ-панели
class AdminStates(StatesGroup):
    admin_password = State()
    broadcast_message = State()
    add_stars = State()

# Веб-сервер для Render
async def web_server():
    app = web.Application()
    app.router.add_get('/', lambda request: web.Response(text="Бот работает! 🚀"))
    return app

# Обработчики бота
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_data:
        users_data[user_id] = {
            'stars': 0.0,
            'referrals': 0,
            'username': message.from_user.username
        }
        stats['total_users'] += 1
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("👤 Профиль", callback_data="profile"))
    keyboard.add(types.InlineKeyboardButton("💫 Рефералка", callback_data="referral"))
    if user_id == 5083696616:  # Замените ADMIN_ID на ваш ID
        keyboard.add(types.InlineKeyboardButton("🛠 Админ-панель", callback_data="admin_panel"))
    
    await message.answer("Добро пожаловать! 🚀", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'profile')
async def show_profile(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user = users_data[user_id]
    
    text = f"🌟 Ваш профиль:\n\n⭐ Звезд: {user['stars']}\n👥 Рефералов: {user['referrals']}"
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("💸 Вывести (от 25⭐)", callback_data="withdraw"))
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
    
    await bot.edit_message_text(text, callback_query.message.chat.id, 
                              callback_query.message.message_id, 
                              reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'referral')
async def show_referral(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    ref_link = f"https://t.me/Ma3stroStarsbot?start={user_id}"
    
    text = f"🎯 Ваша реферальная ссылка:\n\n{ref_link}\n\nЗа каждого реферала вы получаете 0.25⭐"
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
    
    await bot.edit_message_text(text, callback_query.message.chat.id, 
                              callback_query.message.message_id, 
                              reply_markup=keyboard)

# Админ-панель
@dp.callback_query_handler(lambda c: c.data == 'admin_panel')
async def admin_panel(callback_query: types.CallbackQuery):
    await AdminStates.admin_password.set()
    await bot.send_message(callback_query.from_user.id, "Введите пароль:")

@dp.message_handler(state=AdminStates.admin_password)
async def check_admin_password(message: types.Message, state: FSMContext):
    if message.text == "popopo12":
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("📢 Рассылка", callback_data="broadcast"))
        keyboard.add(types.InlineKeyboardButton("📊 Статистика", callback_data="stats"))
        keyboard.add(types.InlineKeyboardButton("📨 Заявки", callback_data="withdraw_requests"))
        keyboard.add(types.InlineKeyboardButton("🎁 Начислить звезды", callback_data="add_stars"))
        await message.answer("Админ-панель:", reply_markup=keyboard)
        await state.finish()
    else:
        await message.answer("Неверный пароль!")
        await state.finish()

# Остальные обработчики админ-панели
@dp.callback_query_handler(lambda c: c.data == 'broadcast')
async def broadcast(callback_query: types.CallbackQuery):
    await AdminStates.broadcast_message.set()
    await bot.send_message(callback_query.from_user.id, "Отправьте сообщение для рассылки:")

@dp.message_handler(state=AdminStates.broadcast_message)
async def send_broadcast(message: types.Message, state: FSMContext):
    for user_id in users_data:
        try:
            await bot.send_message(user_id, message.text)
        except:
            pass
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'stats')
async def show_stats(callback_query: types.CallbackQuery):
    text = f"📊 Статистика:\n\n👥 Пользователей: {stats['total_users']}\n💬 Сообщений сегодня: {stats['messages_today']}"
    await bot.send_message(callback_query.from_user.id, text)

# Запуск веб-сервера и бота
async def on_startup(dp):
    app = await web_server()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)

        text = f"""
👑 **АДМИН ПАНЕЛЬ** 👑

📊 **Статистика бота:**
👥 Пользователей: {self.bot_stats['total_users']}
💰 Всего кликов: {self.bot_stats['total_clicks']:,}
🚫 Заблокировано: {len(self.banned_users)}
⏰ Время работы: {uptime.days}д {uptime.seconds//3600}ч

🛠️ **Управление:**
"""

        keyboard = [
            [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")],
            [InlineKeyboardButton("💰 Начислить клики", callback_data="admin_add_clicks")],
            [
                InlineKeyboardButton("🎫 Создать промо", callback_data="admin_create_promo"),
                InlineKeyboardButton("📋 Список промо", callback_data="admin_list_promos")
            ],
            [
                InlineKeyboardButton("🚫 Заблокировать", callback_data="admin_ban_user"),
                InlineKeyboardButton("✅ Разблокировать", callback_data="admin_unban_user")
            ],
            [InlineKeyboardButton("📋 Список банов", callback_data="admin_ban_list")]
        ]import asyncio
import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Конфигурация
ADMIN_PASSWORD = "14885252"
MAX_CLICK_POWER = 25
MAX_AUTOCLICKER_SPEED = 60  # кликов за 30 секунд
CLICK_COOLDOWN = 15  # кликов до кулдауна
COOLDOWN_TIME = 5  # секунд кулдауна
MYSTERY_BOX_PRICE = 300
REFERRAL_BONUS = 500

class UserData:
    def __init__(self):
        self.clicks = 0
        self.click_power = 1
        self.autoclicker_speed = 0
        self.click_count = 0  # счетчик кликов до кулдауна
        self.cooldown_until = 0
        self.referrals = []
        self.referred_by = None
        self.last_autoclicker = time.time()

class PromoCode:
    def __init__(self, code: str, clicks: int, max_uses: int):
        self.code = code
        self.clicks = clicks
        self.max_uses = max_uses
        self.used_by = []

class TelegramClickerBot:
    def __init__(self, token: str):
        self.token = token
        self.users: Dict[int, UserData] = {}
        self.admins = set()
        self.banned_users = set()
        self.promo_codes: Dict[str, PromoCode] = {}
        self.bot_stats = {
            'total_users': 0,
            'total_clicks': 0,
            'start_time': datetime.now()
        }
        
    def get_user(self, user_id: int) -> UserData:
        if user_id in self.banned_users:
            return None
        if user_id not in self.users:
            self.users[user_id] = UserData()
            self.bot_stats['total_users'] += 1
        return self.users[user_id]

    def process_autoclicker(self, user: UserData):
        """Обработка автокликера"""
        if user.autoclicker_speed > 0:
            current_time = time.time()
            time_diff = current_time - user.last_autoclicker
            
            if time_diff >= 30:  # каждые 30 секунд
                clicks_to_add = user.autoclicker_speed
                user.clicks += clicks_to_add
                user.last_autoclicker = current_time
                self.bot_stats['total_clicks'] += clicks_to_add

    def is_in_cooldown(self, user: UserData) -> bool:
        return time.time() < user.cooldown_until

    def add_click(self, user: UserData) -> bool:
        """Добавляет клик и проверяет кулдаун"""
        if self.is_in_cooldown(user):
            return False
            
        user.clicks += user.click_power
        user.click_count += 1
        self.bot_stats['total_clicks'] += user.click_power
        
        if user.click_count >= CLICK_COOLDOWN:
            user.cooldown_until = time.time() + COOLDOWN_TIME
            user.click_count = 0
            
        return True

    def get_click_upgrade_price(self, current_power: int) -> int:
        return current_power * 100

    def get_autoclicker_upgrade_price(self, current_speed: int) -> int:
        return (current_speed + 1) * 200

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        # Проверка на бан
        if user_id in self.banned_users:
            await update.message.reply_text("🚫 Вы заблокированы в этом боте!")
            return
            
        user = self.get_user(user_id)
        
        # Обработка реферальной системы
        if context.args and len(context.args) > 0:
            try:
                referrer_id = int(context.args[0])
                if referrer_id != user_id and referrer_id in self.users and not user.referred_by:
                    user.referred_by = referrer_id
                    self.users[referrer_id].referrals.append(user_id)
                    self.users[referrer_id].clicks += REFERRAL_BONUS
                    
                    # Уведомление рефереру
                    await context.bot.send_message(
                        referrer_id,
                        f"🎉 У вас новый реферал! Получено {REFERRAL_BONUS} кликов!"
                    )
            except (ValueError, KeyError):
                pass

        await self.show_main_menu(update, context)

    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        # Проверка на бан
        if user_id in self.banned_users:
            await update.message.reply_text("🚫 Вы заблокированы в этом боте!")
            return
            
        user = self.get_user(user_id)
        if not user:
            return
            
        self.process_autoclicker(user)

        cooldown_text = ""
        if self.is_in_cooldown(user):
            remaining = int(user.cooldown_until - time.time()) + 1
            cooldown_text = f"\n❄️ Кулдаун: {remaining}с"

        text = f"""
🎮 **КЛИКЕР БОТ** 🎮

👤 Игрок: {update.effective_user.first_name}
💰 Клики: {user.clicks:,}
⚡ Сила клика: {user.click_power}
🤖 Автокликер: {user.autoclicker_speed}/30с
📊 Кликов до кулдауна: {CLICK_COOLDOWN - user.click_count}
{cooldown_text}

🎯 Выберите действие:
"""

        keyboard = [
            [InlineKeyboardButton("👆 КЛИКАТЬ", callback_data="click")],
            [
                InlineKeyboardButton("🛒 Магазин", callback_data="shop"),
                InlineKeyboardButton("⚡ Улучшения", callback_data="upgrades")
            ],
            [
                InlineKeyboardButton("👥 Рефералы", callback_data="referrals"),
                InlineKeyboardButton("🏆 Топы", callback_data="tops")
            ],
            [InlineKeyboardButton("📊 Профиль", callback_data="profile")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_click(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user = self.get_user(user_id)
        
        if self.add_click(user):
            await update.callback_query.answer(f"💰 +{user.click_power} кликов!")
        else:
            remaining = int(user.cooldown_until - time.time()) + 1
            await update.callback_query.answer(f"❄️ Кулдаун! Осталось: {remaining}с", show_alert=True)
        
        await self.show_main_menu(update, context)

    async def show_shop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user = self.get_user(user_id)

        text = f"""
🛒 **МАГАЗИН** 🛒

💰 Ваши клики: {user.clicks:,}

🎁 Мистери Бокс - {MYSTERY_BOX_PRICE} кликов
Содержимое: 1-1,000 кликов!
"""

        keyboard = [
            [InlineKeyboardButton("🎁 Купить Мистери Бокс", callback_data="buy_mystery_box")],
            [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def buy_mystery_box(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user = self.get_user(user_id)

        if user.clicks >= MYSTERY_BOX_PRICE:
            user.clicks -= MYSTERY_BOX_PRICE
            reward = random.randint(1, 1000)
            user.clicks += reward
            
            await update.callback_query.answer(f"🎁 Вы получили {reward} кликов!", show_alert=True)
        else:
            await update.callback_query.answer("❌ Недостаточно кликов!", show_alert=True)
        
        await self.show_shop(update, context)

    async def show_upgrades(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user = self.get_user(user_id)

        click_price = self.get_click_upgrade_price(user.click_power)
        auto_price = self.get_autoclicker_upgrade_price(user.autoclicker_speed)

        text = f"""
⚡ **УЛУЧШЕНИЯ** ⚡

💰 Ваши клики: {user.clicks:,}

👆 Сила клика: {user.click_power}/{MAX_CLICK_POWER}
💵 Цена улучшения: {click_price:,} кликов

🤖 Автокликер: {user.autoclicker_speed}/{MAX_AUTOCLICKER_SPEED} за 30с
💵 Цена улучшения: {auto_price:,} кликов
"""

        keyboard = []
        
        if user.click_power < MAX_CLICK_POWER:
            keyboard.append([InlineKeyboardButton(f"👆 Улучшить клик ({click_price:,})", callback_data="upgrade_click")])
        
        if user.autoclicker_speed < MAX_AUTOCLICKER_SPEED:
            keyboard.append([InlineKeyboardButton(f"🤖 Улучшить автокликер ({auto_price:,})", callback_data="upgrade_auto")])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def upgrade_click(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user = self.get_user(user_id)
        price = self.get_click_upgrade_price(user.click_power)

        if user.clicks >= price and user.click_power < MAX_CLICK_POWER:
            user.clicks -= price
            user.click_power += 1
            await update.callback_query.answer(f"⚡ Сила клика увеличена до {user.click_power}!")
        else:
            await update.callback_query.answer("❌ Недостаточно кликов или максимальный уровень!", show_alert=True)
        
        await self.show_upgrades(update, context)

    async def upgrade_autoclicker(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user = self.get_user(user_id)
        price = self.get_autoclicker_upgrade_price(user.autoclicker_speed)

        if user.clicks >= price and user.autoclicker_speed < MAX_AUTOCLICKER_SPEED:
            user.clicks -= price
            user.autoclicker_speed += 1
            await update.callback_query.answer(f"🤖 Автокликер улучшен до {user.autoclicker_speed}!")
        else:
            await update.callback_query.answer("❌ Недостаточно кликов или максимальный уровень!", show_alert=True)
        
        await self.show_upgrades(update, context)

    async def show_referrals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user = self.get_user(user_id)

        ref_link = f"https://t.me/your_bot_username?start={user_id}"
        
        text = f"""
👥 **РЕФЕРАЛЬНАЯ СИСТЕМА** 👥

🎁 За каждого реферала: +{REFERRAL_BONUS} кликов
👥 Ваши рефералы: {len(user.referrals)}

🔗 Ваша реферальная ссылка:
`{ref_link}`

Поделитесь ссылкой с друзьями!
"""

        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_tops(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Топ по кликам
        users_by_clicks = sorted(self.users.items(), key=lambda x: x[1].clicks, reverse=True)[:10]
        clicks_top = ""
        for i, (uid, user_data) in enumerate(users_by_clicks, 1):
            try:
                user_info = await context.bot.get_chat(uid)
                name = user_info.first_name or "Неизвестно"
            except:
                name = "Неизвестно"
            clicks_top += f"{i}. {name}: {user_data.clicks:,} кликов\n"

        # Топ по рефералам
        users_by_refs = sorted(self.users.items(), key=lambda x: len(x[1].referrals), reverse=True)[:10]
        refs_top = ""
        for i, (uid, user_data) in enumerate(users_by_refs, 1):
            try:
                user_info = await context.bot.get_chat(uid)
                name = user_info.first_name or "Неизвестно"
            except:
                name = "Неизвестно"
            refs_top += f"{i}. {name}: {len(user_data.referrals)} рефералов\n"

        text = f"""
🏆 **РЕЙТИНГИ** 🏆

💰 **ТОП ПО КЛИКАМ:**
{clicks_top or "Пока никого нет"}

👥 **ТОП ПО РЕФЕРАЛАМ:**
{refs_top or "Пока никого нет"}
"""

        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user = self.get_user(user_id)
        self.process_autoclicker(user)

        text = f"""
📊 **ВАШ ПРОФИЛЬ** 📊

👤 Игрок: {update.effective_user.first_name}
💰 Всего кликов: {user.clicks:,}
⚡ Сила клика: {user.click_power}/{MAX_CLICK_POWER}
🤖 Автокликер: {user.autoclicker_speed}/{MAX_AUTOCLICKER_SPEED} за 30с
👥 Рефералов: {len(user.referrals)}
📊 Кликов до кулдауна: {CLICK_COOLDOWN - user.click_count}
"""

        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def admin_panel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args or context.args[0] != ADMIN_PASSWORD:
            await update.message.reply_text("❌ Неверный пароль!")
            return

        user_id = update.effective_user.id
        self.admins.add(user_id)
        await self.show_admin_panel(update, context)

    async def show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in self.admins:
            await update.message.reply_text("❌ У вас нет доступа!")
            return

        uptime = datetime.now() - self.bot_stats['start_time']
        
        text = f"""
👑 **АДМИН ПАНЕЛЬ** 👑

📊 **Статистика бота:**
👥 Пользователей: {self.bot_stats['total_users']}
💰 Всего кликов: {self.bot_stats['total_clicks']:,}
⏰ Время работы: {uptime.days}д {uptime.seconds//3600}ч

🛠️ **Управление:**
"""

        keyboard = [
            [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")],
            [InlineKeyboardButton("💰 Начислить клики", callback_data="admin_add_clicks")],
            [
                InlineKeyboardButton("🎫 Создать промо", callback_data="admin_create_promo"),
                InlineKeyboardButton("📋 Список промо", callback_data="admin_list_promos")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def promo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("❌ Введите промокод: /promo ВАШ_ПРОМОКОД")
            return

        user_id = update.effective_user.id
        user = self.get_user(user_id)
        promo_code = context.args[0].upper()

        if promo_code not in self.promo_codes:
            await update.message.reply_text("❌ Промокод не найден!")
            return

        promo = self.promo_codes[promo_code]
        
        if user_id in promo.used_by:
            await update.message.reply_text("❌ Вы уже использовали этот промокод!")
            return

        if len(promo.used_by) >= promo.max_uses:
            await update.message.reply_text("❌ Промокод исчерпан!")
            return

        promo.used_by.append(user_id)
        user.clicks += promo.clicks
        
        await update.message.reply_text(f"🎉 Промокод активирован! Получено {promo.clicks:,} кликов!")

    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data == "main_menu":
            await self.show_main_menu(update, context)
        elif query.data == "click":
            await self.handle_click(update, context)
        elif query.data == "shop":
            await self.show_shop(update, context)
        elif query.data == "buy_mystery_box":
            await self.buy_mystery_box(update, context)
        elif query.data == "upgrades":
            await self.show_upgrades(update, context)
        elif query.data == "upgrade_click":
            await self.upgrade_click(update, context)
        elif query.data == "upgrade_auto":
            await self.upgrade_autoclicker(update, context)
        elif query.data == "referrals":
            await self.show_referrals(update, context)
        elif query.data == "tops":
            await self.show_tops(update, context)
        elif query.data == "profile":
            await self.show_profile(update, context)
        # Админ функции
        elif query.data.startswith("admin_"):
            user_id = update.effective_user.id
            if user_id not in self.admins:
                await query.answer("❌ У вас нет доступа!", show_alert=True)
                return
            
            if query.data == "admin_broadcast":
                await query.edit_message_text("📢 Отправьте сообщение для рассылки:")
                context.user_data['waiting_for'] = 'broadcast'
            elif query.data == "admin_add_clicks":
                await query.edit_message_text("💰 Введите ID пользователя и количество кликов через пробел:\nПример: 123456789 1000")
                context.user_data['waiting_for'] = 'add_clicks'
            elif query.data == "admin_create_promo":
                await query.edit_message_text("🎫 Введите данные промокода через пробел:\nФормат: КОД КЛИКИ КОЛИЧЕСТВО_ИСПОЛЬЗОВАНИЙ\nПример: BONUS500 500 10")
                context.user_data['waiting_for'] = 'create_promo'
            elif query.data == "admin_list_promos":
                await self.show_promo_list(update, context)

    async def show_promo_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.promo_codes:
            text = "📋 Промокодов пока нет"
        else:
            text = "📋 **СПИСОК ПРОМОКОДОВ:**\n\n"
            for code, promo in self.promo_codes.items():
                text += f"🎫 `{code}`\n💰 Кликов: {promo.clicks:,}\n📊 Использовано: {len(promo.used_by)}/{promo.max_uses}\n\n"

        keyboard = [
            [InlineKeyboardButton("🔙 Админ панель", callback_data="admin_panel")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if user_id not in self.admins:
            return

        waiting_for = context.user_data.get('waiting_for')
        
        if waiting_for == 'broadcast':
            message = update.message.text
            sent_count = 0
            
            for uid in self.users.keys():
                try:
                    await context.bot.send_message(uid, message)
                    sent_count += 1
                except:
                    pass
            
            await update.message.reply_text(f"📢 Рассылка завершена! Отправлено {sent_count} сообщений.")
            context.user_data['waiting_for'] = None
            
        elif waiting_for == 'add_clicks':
            try:
                parts = update.message.text.split()
                target_id = int(parts[0])
                clicks = int(parts[1])
                
                if target_id in self.users:
                    self.users[target_id].clicks += clicks
                    await update.message.reply_text(f"✅ Пользователю {target_id} начислено {clicks:,} кликов!")
                else:
                    await update.message.reply_text("❌ Пользователь не найден!")
            except:
                await update.message.reply_text("❌ Неверный формат! Используйте: ID КЛИКИ")
            
            context.user_data['waiting_for'] = None
            
        elif waiting_for == 'create_promo':
            try:
                parts = update.message.text.split()
                code = parts[0].upper()
                clicks = int(parts[1])
                max_uses = int(parts[2])
                
                self.promo_codes[code] = PromoCode(code, clicks, max_uses)
                await update.message.reply_text(f"✅ Промокод {code} создан!\n💰 Кликов: {clicks:,}\n📊 Использований: {max_uses}")
            except:
                await update.message.reply_text("❌ Неверный формат! Используйте: КОД КЛИКИ ИСПОЛЬЗОВАНИЯ")
            
            context.user_data['waiting_for'] = None

def main():
    # Замените YOUR_BOT_TOKEN на токен вашего бота
    TOKEN = "YOUR_BOT_TOKEN"
    
    bot = TelegramClickerBot(TOKEN)
    application = Application.builder().token(TOKEN).build()
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("adminpanel", bot.admin_panel_command))
    application.add_handler(CommandHandler("promo", bot.promo_command))
    
    # Обработчики callback'ов
    application.add_handler(CallbackQueryHandler(bot.callback_handler))
    
    # Обработчик сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.message_handler))
    
    print("🚀 Бот запущен!")
    application.run_polling()

if __name__ == "__main__":
    main()
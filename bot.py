# bot.py
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
import os
import aiohttp

# Логи
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Настройки
BOT_TOKEN = "8286347628:AAGn1jX3jB-gnVESPRZlmEeoWg9IFhRnw6M"
ADMIN_CHAT_ID = 1082958705
YKASSA_TOKEN = "test_a-AT5Q8y-jV4fkRKCOYJLXkeKeg-wJzs0L-oN7udAzo"
PORT = int(os.environ.get("PORT", 8000))

# Клавиатура
keyboard = ReplyKeyboardMarkup(
    [
        ["💳 Оплатить 100₽", "💳 Оплатить 500₽"],
        ["📞 Ввести номер телефона", "🛎 Связь с администратором"]
    ],
    resize_keyboard=True
)

# Хранилище номера телефона
user_phone = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 Добро пожаловать в эксклюзивный сервис IT-консультаций!\n\n"
        "🎯 Наши консультации доступны только по рекомендации узкого круга людей.\n"
        "💼 Мы предлагаем экспертные решения для ваших IT-проблем от проверенных специалистов.\n\n"
        "💰 Стоимость консультаций:\n"
        "• 1 консультация: 100 руб.\n"
        "• 12 консультаций: 500 руб. (Вы экономите 700 руб! 🎉)\n\n"
        "Выберите опцию:"
    )
    await update.message.reply_text(welcome_text, reply_markup=keyboard)

# Обработка текста
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id
    name = update.message.from_user.full_name
    phone = user_phone.get(user_id, "Не указан")

    if text == "📞 Ввести номер телефона":
        await update.message.reply_text("Отправьте номер телефона:")
    elif text.startswith("+") or text.isdigit():
        user_phone[user_id] = text
        await update.message.reply_text(f"Телефон {text} сохранен ✅")
    elif text in ["💳 Оплатить 100₽", "💳 Оплатить 500₽"]:
        amount = 100 if "100" in text else 500
        # Отправляем админу форму заказа
        order_text = f"Новый заказ:\nИмя: {name}\nТелеграм ID: {user_id}\nТелефон: {phone}\nСумма: {amount}₽"
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=order_text)
        await update.message.reply_text(f"Ваш заказ на {amount}₽ принят ✅")
    elif text == "🛎 Связь с администратором":
        await update.message.reply_text(f"Связь с администратором: @{ADMIN_CHAT_ID}")
    else:
        await update.message.reply_text("Выберите опцию из меню", reply_markup=keyboard)

# Основной запуск
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Запуск webhook на Render
    import uvicorn
    uvicorn.run("bot:app", host="0.0.0.0", port=PORT, log_level="info")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

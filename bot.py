import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
import os
from aiohttp import web

# --- Настройки ---
BOT_TOKEN = "8286347628:AAGn1jX3jB-gnVESPRZlmEeoWg9IFhRnw6M"
ADMIN_CHAT_ID = 1082958705
YKASSA_TOKEN = "test_a-AT5Q8y-jV4fkRKCOYJLXkeKeg-wJzs0L-oN7udAzo"
PORT = int(os.environ.get("PORT", 8000))

# --- Логирование ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Состояния для ConversationHandler ---
ASK_PHONE = 1
ASK_PAYMENT = 2

# --- Приветственное сообщение ---
WELCOME_TEXT = (
    "👋 Добро пожаловать в эксклюзивный сервис IT-консультаций!\n\n"
    "🎯 Наши консультации доступны только по рекомендации узкого круга людей.\n"
    "💼 Мы предлагаем экспертные решения для ваших IT-проблем от проверенных специалистов.\n\n"
    "💰 Стоимость консультаций:\n"
    "• 1 консультация: 100 руб.\n"
    "• 12 консультаций: 500 руб. (Вы экономите 700 руб! 🎉)\n\n"
    "Выберите опцию:"
)

# --- Клавиатура ---
def main_keyboard():
    keyboard = [
        [KeyboardButton("Оплатить 100₽"), KeyboardButton("Оплатить 500₽")],
        [KeyboardButton("Ввести номер телефона", request_contact=True)],
        [KeyboardButton("Связь с администратором")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- Обработчики ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_TEXT, reply_markup=main_keyboard())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user

    if text == "Связь с администратором":
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"Пользователь хочет связаться с администратором:\n"
                 f"ID: {user.id}\nИмя: {user.full_name}"
        )
        await update.message.reply_text("Администратор уведомлен и свяжется с вами.")
    
    elif text in ["Оплатить 100₽", "Оплатить 500₽"]:
        amount = 100 if text.endswith("100₽") else 500
        await update.message.reply_text(f"Вы выбрали оплату {amount}₽. Отправьте номер телефона ниже для завершения заказа.")

    elif update.message.contact:
        phone = update.message.contact.phone_number
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"Новая оплата:\n"
                 f"Пользователь: {user.full_name}\n"
                 f"Telegram ID: {user.id}\n"
                 f"Телефон: {phone}\n"
                 f"Сумма: {context.user_data.get('payment_amount', 'Не выбрана')}"
        )
        await update.message.reply_text("Спасибо! Ваша информация отправлена администратору.")

# --- Webhook для Render ---
async def webhook(request):
    data = await request.json()
    update = Update.de_json(data, app.bot)
    await app.bot.process_update(update)
    return web.Response(text="OK")

# --- Основная функция ---
async def main():
    global app
    app = web.Application()
    app.router.add_post(f"/webhook/{BOT_TOKEN}", webhook)

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    logger.info(f"Bot running on port {PORT}")
    while True:
        await asyncio.sleep(3600)  # Keep alive

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

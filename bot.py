import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# --- Настройки ---
TELEGRAM_TOKEN = "8286347628:AAGn1jX3jB-gnVESPRZlmEeoWg9IFhRnw6M"
ADMIN_CHAT_ID = 1082958705
YOOKASSA_TOKEN = "test_a-AT5Q8y-jV4fkRKCOYJLXkeKeg-wJzs0L-oN7udAzo"

PORT = 8000

# --- Логирование ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Клавиатура ---
keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("💵 Оплатить 100₽"), KeyboardButton("💵 Оплатить 500₽")],
    [KeyboardButton("📞 Ввести номер телефона", request_contact=True)],
    [KeyboardButton("👤 Связь с администратором")]
], resize_keyboard=True)


# --- Команды ---
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


# --- Обработка кнопок ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user

    if text in ["💵 Оплатить 100₽", "💵 Оплатить 500₽"]:
        amount = 100 if text.endswith("100₽") else 500
        await update.message.reply_text(f"Вы выбрали оплату {amount}₽. Ссылка на оплату через ЮKassa будет здесь.")
        # Здесь можно вставить интеграцию с ЮKassa API
        await notify_admin(user.id, user.full_name, None, amount)

    elif text == "👤 Связь с администратором":
        await update.message.reply_text(f"Администратор: @{ADMIN_CHAT_ID}")

    elif text == "📞 Ввести номер телефона":
        await update.message.reply_text("Нажмите кнопку ниже, чтобы отправить ваш номер телефона.")

    elif update.message.contact:
        phone = update.message.contact.phone_number
        await update.message.reply_text(f"Спасибо! Ваш номер {phone} получен.")
        await notify_admin(user.id, user.full_name, phone, None)


# --- Функция уведомления администратора ---
async def notify_admin(user_id, full_name, phone, amount):
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    message = f"Новый заказ:\nID: {user_id}\nИмя: {full_name}\n"
    if phone:
        message += f"Телефон: {phone}\n"
    if amount:
        message += f"Сумма оплаты: {amount}₽"
    await app.bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)


# --- Основной запуск ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT | filters.CONTACT, handle_message))

    # Для Render используем webhook (укажи свой URL)
    RENDER_URL = "https://tgbotwb.onrender.com"
    WEBHOOK_PATH = f"/webhook/{TELEGRAM_TOKEN}"

    import asyncio
    import uvicorn
    from fastapi import FastAPI, Request

    fast_app = FastAPI()

    @fast_app.post(WEBHOOK_PATH)
    async def telegram_webhook(req: Request):
        body = await req.json()
        update = Update.de_json(body)
        await app.update_queue.put(update)
        return {"ok": True}

    @fast_app.get("/health")
    async def health():
        return {"status": "ok"}

    uvicorn.run(fast_app, host="0.0.0.0", port=PORT)

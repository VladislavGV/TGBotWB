# bot.py
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8286347628:AAGn1jX3jB-gnVESPRZlmEeoWg9IFhRnw6M"
ADMIN_CHAT_ID = 1082958705
YUKASSA_TOKEN = "test_a-AT5Q8y-jV4fkRKCOYJLXkeKeg-wJzs0L-oN7udAzo"
PORT = int(os.environ.get("PORT", 8000))
WEBHOOK_URL = f"https://tgbotwb.onrender.com/webhook/{BOT_TOKEN}"

keyboard = ReplyKeyboardMarkup(
    [
        ["💳 Оплатить 100₽", "💳 Оплатить 500₽"],
        ["📞 Ввести номер телефона", "🛎 Связь с администратором"]
    ],
    resize_keyboard=True
)

user_phone = {}

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
        order_text = (
            f"Новый заказ:\n"
            f"Имя: {name}\n"
            f"Телеграм ID: {user_id}\n"
            f"Телефон: {phone}\n"
            f"Сумма: {amount}₽"
        )
        # Отправка админу
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=order_text)
        await update.message.reply_text(f"Ваш заказ на {amount}₽ принят ✅")
        # Здесь можно добавить интеграцию с ЮKassa
    elif text == "🛎 Связь с администратором":
        await update.message.reply_text(f"Связь с администратором: @{ADMIN_CHAT_ID}")
    else:
        await update.message.reply_text("Выберите опцию из меню", reply_markup=keyboard)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Запуск webhook сервера
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=WEBHOOK_URL
    )
    
from fastapi import FastAPI
from bot_logic import start_webhook  # логика твоего бота в отдельном файле

app = FastAPI()

@app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: dict):
    await start_webhook(token, request)
    return {"ok": True}

@app.get("/health")
async def health():
    return {"status": "ok"}

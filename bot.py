from fastapi import FastAPI, Request
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# === Настройки ===
BOT_TOKEN = "8286347628:AAGn1jX3jB-gnVESPRZlmEeoWg9IFhRnw6M"
ADMIN_CHAT_ID = 1082958705
YKASSA_TOKEN = "test_a-AT5Q8y-jV4fkRKCOYJLXkeKeg-wJzs0L-oN7udAzo"

app = FastAPI()
application = ApplicationBuilder().token(BOT_TOKEN).build()

# === Клавиатура ===
keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("Оплатить 100₽"), KeyboardButton("Оплатить 500₽")],
    [KeyboardButton("Ввести номер телефона", request_contact=True)],
    [KeyboardButton("Связь с администратором")]
], resize_keyboard=True)

# === Команда /start ===
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

# === Обработка сообщений ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user
    contact = update.message.contact.phone_number if update.message.contact else None

    if text in ["Оплатить 100₽", "Оплатить 500₽"]:
        # TODO: тут интеграция ЮKassa
        amount = 100 if text == "Оплатить 100₽" else 500
        await update.message.reply_text(f"Вы выбрали оплату {amount}₽. (Интеграция ЮKassa здесь)")
        # Отправка админу
        await application.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"Новый заказ:\nID: {user.id}\nИмя: {user.first_name}\nТелефон: {contact}\nСумма: {amount}₽"
        )

    elif text == "Связь с администратором":
        await update.message.reply_text("Администратор свяжется с вами скоро.")
        await application.bot.send_message(chat_id=ADMIN_CHAT_ID,
                                           text=f"Пользователь {user.first_name} ({user.id}) хочет связаться с админом.")

# === Добавляем хэндлеры ===
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT | filters.CONTACT, handle_message))

# === Webhook ===
@app.post(f"/webhook/{BOT_TOKEN}")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return {"ok": True}

# === Запуск сервера ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

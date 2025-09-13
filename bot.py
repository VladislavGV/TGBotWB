import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
import requests

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
YUKASSA_TOKEN = os.getenv("YUKASSA_TOKEN")
PORT = int(os.getenv("PORT", 8000))

# FastAPI
app = FastAPI()
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Константы для ConversationHandler
ASK_PHONE = 1

# Клавиатура
def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("Оплатить 100₽", callback_data="pay_100")],
        [InlineKeyboardButton("Оплатить 500₽", callback_data="pay_500")],
        [InlineKeyboardButton("Связь с администратором", callback_data="contact_admin")],
        [KeyboardButton("Ввести номер телефона", request_contact=True)]
    ]
    return keyboard

# /start команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = main_keyboard()
    reply_markup = ReplyKeyboardMarkup(
        [[KeyboardButton("Ввести номер телефона", request_contact=True)]], resize_keyboard=True
    )
    await update.message.reply_text(
        f"Привет {update.effective_user.first_name}! Выберите действие:",
        reply_markup=reply_markup
    )

# Обработка кнопок Inline
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user

    if query.data.startswith("pay_"):
        amount = int(query.data.split("_")[1])
        await query.message.reply_text(f"Вы выбрали оплату {amount}₽. Ссылка на оплату через ЮKassa:")
        # Пример ссылки, можно заменить на реальный вызов API ЮKassa
        pay_link = f"https://yookassa.ru/pay?amount={amount}&token={YUKASSA_TOKEN}&user_id={user.id}"
        await query.message.reply_text(pay_link)
        # Отправка админу
        await application.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"Новый заказ:\nПользователь: {user.full_name}\nID: {user.id}\nСумма: {amount}₽"
        )

    elif query.data == "contact_admin":
        await query.message.reply_text(f"Связь с администратором: https://t.me/{ADMIN_CHAT_ID}")

# Обработка контакта
async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user = update.effective_user
    phone = contact.phone_number if contact else "Не предоставлен"
    await update.message.reply_text(f"Спасибо! Ваш номер: {phone}")
    await application.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"Пользователь {user.full_name} ({user.id}) предоставил номер телефона: {phone}"
    )

# Webhook endpoint
@app.post(f"/webhook/{BOT_TOKEN}")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return {"ok": True}

# /start обработчик
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_handler))
application.add_handler(MessageHandler(filters.CONTACT, contact_handler))

# Запуск Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bot:app", host="0.0.0.0", port=PORT, log_level="info")

import os
from fastapi import FastAPI, Request
from telegram import (
    Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
)
from telegram.constants import ParseMode
import logging

# ----------------------- Настройки -----------------------
BOT_TOKEN = "8286347628:AAGn1jX3jB-gnVESPRZlmEeoWg9IFhRnw6M"
ADMIN_CHAT_ID = 1082958705
YOO_KASSA_TOKEN = "test_a-AT5Q8y-jV4fkRKCOYJLXkeKeg-wJzs0L-oN7udAzo"
PORT = int(os.environ.get("PORT", 8000))

logging.basicConfig(level=logging.INFO)

# ----------------------- Инициализация бота -----------------------
app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
app = FastAPI()

# ----------------------- Команды -----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Клавиатура с кнопками оплаты, контакта и связи с админом
    keyboard = [
        [InlineKeyboardButton("💵 Оплатить 100₽", callback_data="pay_100")],
        [InlineKeyboardButton("💵 Оплатить 500₽", callback_data="pay_500")],
        [KeyboardButton("📞 Ввести номер телефона", request_contact=True)],
        [InlineKeyboardButton("✉ Связь с администратором", callback_data="contact_admin")]
    ]

    reply_markup = ReplyKeyboardMarkup(
        [[KeyboardButton("📞 Ввести номер телефона", request_contact=True)]],
        resize_keyboard=True
    )

    inline_markup = InlineKeyboardMarkup(keyboard[:3] + [keyboard[3]])

    await update.message.reply_text(
        f"Привет, {user.first_name}! Выберите действие:",
        reply_markup=inline_markup
    )

# ----------------------- Обработка кнопок -----------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user

    if query.data == "contact_admin":
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"Пользователь {user.first_name} @{user.username} хочет связаться с администратором"
        )
        await query.edit_message_text("Администратор будет с вами на связи!")
    
    elif query.data.startswith("pay_"):
        amount = int(query.data.split("_")[1])
        await query.edit_message_text(f"Вы выбрали оплату {amount}₽. Ссылка на оплату отправлена в ЛС!")
        
        # Формирование ссылки для ЮKassa (пример)
        payment_url = f"https://yoomoney.ru/pay?receiver={YOO_KASSA_TOKEN}&sum={amount}"
        await context.bot.send_message(chat_id=user.id, text=f"Перейдите по ссылке для оплаты:\n{payment_url}")

# ----------------------- Обработка контакта -----------------------
async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user = update.message.from_user

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=(
            f"Новая информация о клиенте:\n"
            f"Имя: {user.first_name}\n"
            f"Telegram ID: {user.id}\n"
            f"Телефон: {contact.phone_number}"
        )
    )

    await update.message.reply_text("Спасибо! Ваш номер отправлен администратору.")

# ----------------------- Webhook -----------------------
@app.post("/webhook/{token}")
async def webhook(request: Request, token: str):
    if token != BOT_TOKEN:
        return {"ok": False, "error": "Invalid token"}
    
    data = await request.json()
    update = Update.de_json(data, app_bot.bot)
    await app_bot.update_queue.put(update)
    return {"ok": True}

# ----------------------- Добавление обработчиков -----------------------
app_bot.add_handler(CommandHandler("start", start))
app_bot.add_handler(CallbackQueryHandler(button_handler))
app_bot.add_handler(MessageHandler(filters.CONTACT, contact_handler))

# ----------------------- Запуск Uvicorn -----------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)

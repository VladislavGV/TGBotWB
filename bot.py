import logging
import os
from fastapi import FastAPI, Request
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import aiohttp

# ===================== Настройки =====================
BOT_TOKEN = "8286347628:AAGn1jX3jB-gnVESPRZlmEeoWg9IFhRnw6M"
ADMIN_CHAT_ID = 1082958705
YUKASSA_TOKEN = "test_a-AT5Q8y-jV4fkRKCOYJLXkeKeg-wJzs0L-oN7udAzo"
PORT = int(os.environ.get("PORT", 8000))

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ===================== Клавиатуры =====================
def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("Оплатить 100₽", callback_data="pay_100"),
         InlineKeyboardButton("Оплатить 500₽", callback_data="pay_500")],
        [InlineKeyboardButton("Связь с администратором", callback_data="contact_admin")],
    ]
    return InlineKeyboardMarkup(keyboard)

def contact_keyboard():
    keyboard = [
        [KeyboardButton("Ввести номер телефона", request_contact=True)]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

# ===================== FastAPI =====================
app = FastAPI()
bot = Bot(token=BOT_TOKEN)

# ===================== Обработчики =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Выберите действие:",
        reply_markup=main_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "pay_100":
        await process_payment(update, context, 100)
    elif query.data == "pay_500":
        await process_payment(update, context, 500)
    elif query.data == "contact_admin":
        await query.message.reply_text(
            f"Связь с администратором: https://t.me/{ADMIN_CHAT_ID}",
            reply_markup=contact_keyboard()
        )

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user_name = update.message.from_user.full_name
    user_id = update.message.from_user.id
    phone = contact.phone_number

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"Новый контакт!\nИмя: {user_name}\nTelegram ID: {user_id}\nТелефон: {phone}"
    )
    
    await update.message.reply_text("Спасибо! Контакт сохранен.")

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, amount: int):
    user = update.callback_query.from_user
    user_id = user.id
    user_name = user.full_name

    headers = {
        "Authorization": f"Bearer {YUKASSA_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "amount": {"value": str(amount), "currency": "RUB"},
        "confirmation": {"type": "redirect", "return_url": "https://tgbotwb.onrender.com"},
        "capture": True,
        "description": f"Оплата {amount}₽ пользователем {user_name}"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.yookassa.ru/v3/payments", headers=headers, json=data) as resp:
            result = await resp.json()
            payment_url = result.get("confirmation", {}).get("confirmation_url", "https://yookassa.ru")

    await update.callback_query.message.reply_text(f"Перейдите для оплаты: {payment_url}")

    # Отправка админу
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"Новый заказ!\nИмя: {user_name}\nTelegram ID: {user_id}\nСумма: {amount}₽"
    )

# ===================== Webhook =====================
@app.post("/webhook/{token}")
async def webhook(request: Request, token: str):
    if token != BOT_TOKEN:
        return {"ok": False, "error": "Invalid token"}
    
    data = await request.json()
    update = Update.de_json(data, bot)

    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    app_bot.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    
    await app_bot.update_queue.put(update)
    return {"ok": True}

# ===================== Healthcheck =====================
@app.get("/health")
async def health():
    return {"status": "ok"}

# ===================== Запуск =====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)

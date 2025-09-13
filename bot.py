import os
import logging
from fastapi import FastAPI, Request
from telegram import (
    Update, LabeledPrice, KeyboardButton,
    ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, PreCheckoutQueryHandler, filters
)

# --- Логирование ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Константы ---
TOKEN = "8286347628:AAGn1jX3jB-gnVESPRZlmEeoWg9IFhRnw6M"
YKASSA_TOKEN = "test_a-AT5Q8y-jV4fkRKCOYJLXkeKeg-wJzs0L-oN7udAzo"
ADMIN_CHAT_ID = 1082958705
PORT = int(os.environ.get("PORT", 8000))

# --- Conversation states ---
SELECTING_ACTION, GETTING_PHONE, GETTING_PLATFORM = range(3)

# --- FastAPI ---
app = FastAPI()

# --- Бот функции ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [KeyboardButton("Купить 1 консультацию"), KeyboardButton("Купить 12 консультаций")],
        [KeyboardButton("Связь с администратором", url=f"https://t.me/{ADMIN_CHAT_ID}")]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text(
        "👋 Добро пожаловать в IT-консультации!\nВыберите опцию ниже:",
        reply_markup=reply_markup
    )
    return SELECTING_ACTION

async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == "Связь с администратором":
        await update.message.reply_text(f"Связь с администратором: https://t.me/{ADMIN_CHAT_ID}")
        return ConversationHandler.END

    context.user_data['consultation_type'] = text
    context.user_data['price'] = 100 if text == "Купить 1 консультацию" else 500

    # Кнопка для автоматического запроса контакта
    contact_button = KeyboardButton("Отправить номер телефона", request_contact=True)
    keyboard = [[contact_button]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Нажмите кнопку ниже, чтобы автоматически отправить ваш номер телефона:",
        reply_markup=reply_markup
    )
    return GETTING_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact = update.message.contact
    if contact:
        context.user_data['phone'] = contact.phone_number
    else:
        context.user_data['phone'] = update.message.text  # fallback если пользователь пишет вручную

    await update.message.reply_text("Укажите вашу платформу (iOS или Android):")
    return GETTING_PLATFORM

async def get_platform(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['platform'] = update.message.text

    prices = [LabeledPrice(label=context.user_data['consultation_type'], amount=context.user_data['price']*100)]

    await context.bot.send_invoice(
        chat_id=update.effective_chat.id,
        title=context.user_data['consultation_type'],
        description=f"{context.user_data['consultation_type']} IT консультация",
        payload=f"{context.user_data['consultation_type']}|{context.user_data['phone']}|{context.user_data['platform']}",
        provider_token=YKASSA_TOKEN,
        currency="RUB",
        prices=prices,
        start_parameter="consultation_order"
    )
    return ConversationHandler.END

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.pre_checkout_query:
        await update.pre_checkout_query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment_info = update.message.successful_payment
    payload_parts = payment_info.invoice_payload.split('|')
    await update.message.reply_text(
        f"✅ Оплата прошла успешно!\n"
        f"Услуга: {payload_parts[0]}\n"
        f"Телефон: {payload_parts[1]}\n"
        f"Платформа: {payload_parts[2]}\n"
        f"Сумма: {payment_info.total_amount/100} руб."
    )
    # Уведомление администратору
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"🛎 Новый заказ!\nУслуга: {payload_parts[0]}\nТелефон: {payload_parts[1]}\nПлатформа: {payload_parts[2]}\nСумма: {payment_info.total_amount/100} руб.\nПользователь: @{update.effective_user.username}"
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Заказ отменен.")
    return ConversationHandler.END

# --- Настройка Application ---
application = Application.builder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        SELECTING_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_action)],
        GETTING_PHONE: [MessageHandler(filters.CONTACT | (filters.TEXT & ~filters.COMMAND), get_phone)],
        GETTING_PLATFORM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_platform)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

application.add_handler(conv_handler)
application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

# --- Webhook endpoint ---
@app.post("/webhook/{token}")
async def webhook(token: str, request: Request):
    if token != TOKEN:
        return {"ok": False, "error": "Unauthorized"}
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return {"ok": True}

# --- Health check ---
@app.get("/health")
async def health():
    return {"status": "ok"}

# --- Запуск локально ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)

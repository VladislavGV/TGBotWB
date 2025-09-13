# bot.py
import logging
from fastapi import FastAPI, Request
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# -------------------- Настройки --------------------
TELEGRAM_TOKEN = "8286347628:AAGn1jX3jB-gnVESPRZlmEeoWg9IFhRnw6M"
ADMIN_CHAT_ID = 1082958705
YOOKASSA_TOKEN = "test_a-AT5Q8y-jV4fkRKCOYJLXkeKeg-wJzs0L-oN7udAzo"

# -------------------- Логирование --------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# -------------------- FastAPI --------------------
app = FastAPI()
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# -------------------- Клавиатура --------------------
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("Оплатить 100₽"), KeyboardButton("Оплатить 500₽")],
        [KeyboardButton("Ввести номер телефона", request_contact=True)],
        [KeyboardButton("Связь с администратором")]
    ],
    resize_keyboard=True
)

# -------------------- Команды --------------------
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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    first_name = update.message.from_user.first_name
    contact = update.message.contact.phone_number if update.message.contact else None

    if text == "Связь с администратором":
        await application.bot.send_message(
            chat_id=user_id,
            text="Администратор свяжется с вами в ближайшее время."
        )
        await application.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"Пользователь @{username} ({first_name}, ID: {user_id}) хочет связаться с администратором."
        )
    elif text in ["Оплатить 100₽", "Оплатить 500₽"]:
        amount = 100 if text == "Оплатить 100₽" else 500
        await application.bot.send_message(
            chat_id=user_id,
            text=f"Ссылка на оплату {amount}₽ через ЮKassa: https://yookassa.ru/payments-test?amount={amount}"
        )
        # Отправка админу
        await application.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"Новый заказ:\nПользователь: @{username} ({first_name})\nID: {user_id}\nСумма: {amount}₽\nТелефон: {contact or 'не указан'}"
        )

# -------------------- Обработчики --------------------
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT | filters.CONTACT, handle_message))

# -------------------- Webhook --------------------
@app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    if token != TELEGRAM_TOKEN:
        return {"ok": False, "error": "Invalid token"}
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return {"ok": True}

# -------------------- Healthcheck --------------------
@app.get("/health")
async def health():
    return {"status": "ok"}

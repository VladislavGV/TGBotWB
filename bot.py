import os
from fastapi import FastAPI, Request
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import requests

BOT_TOKEN = "8286347628:AAGn1jX3jB-gnVESPRZlmEeoWg9IFhRnw6M"
ADMIN_CHAT_ID = 1082958705
YKASSA_SHOP_ID = "test_a-AT5Q8y-jV4fkRKCOYJLXkeKeg-wJzs0L-oN7udAzo"
YKASSA_SECRET_KEY = "test_secret_key"  # Если есть, можно добавить

app = FastAPI()

# Telegram application
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Клавиатура
keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton("Оплатить 100₽"), KeyboardButton("Оплатить 500₽")],
        [KeyboardButton("Ввести номер телефона", request_contact=True)],
        [KeyboardButton("Связь с администратором")]
    ],
    resize_keyboard=True
)

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
    user_name = update.message.from_user.full_name
    phone = update.message.contact.phone_number if update.message.contact else "не указан"

    if text in ["Оплатить 100₽", "Оплатить 500₽"]:
        amount = 10000 if text == "Оплатить 100₽" else 50000  # копейки
        payment = create_ykassa_payment(amount, f"Консультация {text}")
        await update.message.reply_text(f"Ссылка на оплату: {payment}")
        notify_admin(user_id, user_name, phone, amount/100)
    elif text == "Ввести номер телефона":
        await update.message.reply_text("Нажмите кнопку ниже и поделитесь контактом.")
    elif text == "Связь с администратором":
        await update.message.reply_text("Вы можете написать администратору: t.me/YourAdminUsername")
    else:
        await update.message.reply_text("Выберите одну из опций на клавиатуре.", reply_markup=keyboard)

def create_ykassa_payment(amount, description):
    """
    Создание тестовой ссылки на оплату ЮKassa (тестовый вариант)
    """
    url = "https://payment.yookassa.ru/create_payment_link"
    payload = {
        "shopId": YKASSA_SHOP_ID,
        "amount": {"value": str(amount/100), "currency": "RUB"},
        "description": description,
        "test": True
    }
    # Токен авторизации
    headers = {"Authorization": f"Bearer {YKASSA_SECRET_KEY}"}
    # Для теста вернём имитацию ссылки
    return f"https://yookassa_test_payment_link.com/pay?amount={amount/100}"

def notify_admin(user_id, user_name, phone, amount):
    text = f"Новая оплата!\n\nID: {user_id}\nИмя: {user_name}\nТелефон: {phone}\nСумма: {amount} ₽"
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={
        "chat_id": ADMIN_CHAT_ID,
        "text": text
    })

# Роут для Telegram Webhook
@app.post(f"/webhook/{BOT_TOKEN}")
async def telegram_webhook(request: Request):
    body = await request.json()
    update = Update.de_json(body, application.bot)
    await application.update_queue.put(update)
    return {"ok": True}

# Запуск бота в Render
@app.on_event("startup")
async def on_startup():
    # Запускаем обработку очереди обновлений
    import asyncio
    asyncio.create_task(application.initialize())

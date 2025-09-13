import logging
import json
import base64
from aiohttp import web, ClientSession
from telegram import Bot, Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Dispatcher, CallbackContext

# --- Настройки ---
TOKEN = "8286347628:AAGn1jX3jB-gnVESPRZlmEeoWg9IFhRnw6M"
ADMIN_CHAT_ID = 1082958705
YUKASSA_SHOP_ID = "test_a-AT5Q8y-jV4fkRKCOYJLXkeKeg-wJzs0L-oN7udAzo"
YUKASSA_TOKEN = "test_a-AT5Q8y-jV4fkRKCOYJLXkeKeg-wJzs0L-oN7udAzo"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)

# --- Клавиатура ---
keyboard = [
    [KeyboardButton("Оплатить 100₽"), KeyboardButton("Оплатить 500₽")],
    [KeyboardButton("Ввести номер телефона", request_contact=True)],
    [KeyboardButton("Связь с администратором")]
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- Словарь для хранения данных клиента перед оплатой ---
pending_payments = {}

# --- Приветственное сообщение ---
async def start(update: Update, context: CallbackContext = None):
    welcome_text = (
        "👋 Добро пожаловать в эксклюзивный сервис IT-консультаций!\n\n"
        "🎯 Наши консультации доступны только по рекомендации узкого круга людей.\n"
        "💼 Мы предлагаем экспертные решения для ваших IT-проблем от проверенных специалистов.\n\n"
        "💰 Стоимость консультаций:\n"
        "• 1 консультация: 100 руб.\n"
        "• 12 консультаций: 500 руб. (Вы экономите 700 руб! 🎉)\n\n"
        "Выберите опцию:"
    )
    await bot.send_message(chat_id=update.message.chat_id, text=welcome_text, reply_markup=reply_markup)

# --- Создание платежа через ЮKassa ---
async def create_yukassa_payment(user_id: int, amount: int, username: str):
    url = "https://api.yookassa.ru/v3/payments"
    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{YUKASSA_SHOP_ID}:{YUKASSA_TOKEN}'.encode()).decode()}",
        "Content-Type": "application/json"
    }
    data = {
        "amount": {"value": str(amount), "currency": "RUB"},
        "confirmation": {"type": "redirect", "return_url": "https://tgbotwb.onrender.com"},
        "capture": True,
        "description": f"Оплата {amount}₽ пользователем {username} ({user_id})"
    }
    async with ClientSession() as session:
        async with session.post(url, headers=headers, data=json.dumps(data)) as resp:
            result = await resp.json()
            pending_payments[result["id"]] = {"user_id": user_id, "username": username, "amount": amount}
            return result.get("confirmation", {}).get("confirmation_url")

# --- Обработка сообщений пользователя ---
async def handle_message(update, context=None):
    text = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.full_name
    contact = update.message.contact.phone_number if update.message.contact else None

    if text == "Связь с администратором":
        await bot.send_message(chat_id=user_id, text="Администратор свяжется с вами скоро.")
        await bot.send_message(chat_id=ADMIN_CHAT_ID,
                               text=f"Пользователь {username} ({user_id}) хочет связаться с администратором.")

    elif text in ["Оплатить 100₽", "Оплатить 500₽"]:
        amount = 100 if "100" in text else 500
        payment_url = await create_yukassa_payment(user_id, amount, username)
        if payment_url:
            await bot.send_message(chat_id=user_id, text=f"Перейдите по ссылке для оплаты: {payment_url}")
        else:
            await bot.send_message(chat_id=user_id, text="Ошибка при создании платежа, попробуйте позже.")

    elif update.message.contact:
        await bot.send_message(chat_id=user_id, text=f"Спасибо! Ваш номер {contact} сохранен.")

# --- Webhook Telegram ---
async def handle_telegram_webhook(request):
    data = await request.json()
    update = Update.de_json(data, bot)
    await handle_message(update)
    return web.Response(text="ok")

# --- Webhook ЮKassa ---
async def handle_yukassa_webhook(request):
    data = await request.json()
    payment_id = data.get("object", {}).get("id")
    status = data.get("object", {}).get("status")

    if status == "succeeded" and payment_id in pending_payments:
        info = pending_payments.pop(payment_id)
        await bot.send_message(chat_id=ADMIN_CHAT_ID,
                               text=f"Новая успешная оплата!\n"
                                    f"Пользователь: {info['username']}\n"
                                    f"ID: {info['user_id']}\n"
                                    f"Сумма: {info['amount']}₽")
    return web.Response(text="ok")

# --- ASGI app ---
app = web.Application()
app.router.add_post(f"/webhook/{TOKEN}", handle_telegram_webhook)
app.router.add_post("/yukassa-webhook", handle_yukassa_webhook)

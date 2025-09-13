from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
import aiohttp

ADMIN_CHAT_ID = 1082958705
YKASSA_TOKEN = "test_a-AT5Q8y-jV4fkRKCOYJLXkeKeg-wJzs0L-oN7udAzo"
YKASSA_SHOP_ID = "your_shop_id_here"  # Замени на ID магазина из ЮKassa

def start_keyboard():
    keyboard = [
        ["💳 100₽", "💳 500₽"],
        ["🛠 Связаться с поддержкой"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def handle_buy(update, context, amount):
    phone_keyboard = [[KeyboardButton("Ввести номер телефона", request_contact=True)]]
    await update.message.reply_text(
        f"Вы выбрали оплату {amount}₽. Пожалуйста, введите ваш номер телефона:",
        reply_markup=ReplyKeyboardMarkup(phone_keyboard, resize_keyboard=True)
    )
    context.user_data['amount'] = amount

async def handle_phone(update, context):
    contact = update.message.contact
    context.user_data['phone'] = contact.phone_number
    context.user_data['user_id'] = update.effective_user.id

    platform_keyboard = [["iOS"], ["Android"]]
    await update.message.reply_text(
        "Выберите платформу вашего телефона:",
        reply_markup=ReplyKeyboardMarkup(platform_keyboard, resize_keyboard=True)
    )

async def handle_platform(update, context):
    platform = update.message.text
    context.user_data['platform'] = platform

    message = (
        f"Новый заказ:\n"
        f"ID: {context.user_data['user_id']}\n"
        f"Телефон: {context.user_data['phone']}\n"
        f"Платформа: {platform}\n"
        f"Сумма: {context.user_data['amount']}₽"
    )

    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)

    # Создание платежа через ЮKassa
    async with aiohttp.ClientSession() as session:
        payload = {
            "amount": {"value": str(context.user_data['amount']), "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": "https://tgbotwb.onrender.com"},
            "capture": True,
            "description": f"Оплата консультации {context.user_data['amount']}₽"
        }
        headers = {
            "Authorization": f"Basic {YKASSA_TOKEN}",
            "Content-Type": "application/json"
        }
        async with session.post(f"https://api.yookassa.ru/v3/payments", json=payload, headers=headers) as resp:
            data = await resp.json()
            await update.message.reply_text(f"Перейдите для оплаты: {data['confirmation']['confirmation_url']}")

async def handle_support(update, context):
    text = f"Пользователь {update.effective_user.first_name} хочет связаться с поддержкой."
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)
    await update.message.reply_text("Сообщение отправлено администратору.")

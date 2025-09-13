from telegram import Update
from telegram.ext import ContextTypes
import requests

async def handle_support(update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: int):
    user = update.message.from_user
    msg = f"⚠️ Пользователь {user.first_name} @{user.username} ({user.id}) просит поддержку"
    await context.bot.send_message(chat_id=admin_id, text=msg)
    await update.message.reply_text("✅ Ваше сообщение отправлено администратору.")

async def handle_buy(update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: int, yukassa_token: str):
    data = context.user_data
    # Сообщение админу
    msg = (
        f"💰 Новый заказ!\n"
        f"👤 Пользователь: {update.message.from_user.first_name}\n"
        f"🆔 Telegram ID: {data['user_id']}\n"
        f"📲 Телефон: {data['phone']}\n"
        f"📱 Платформа: {data['platform']}\n"
        f"💳 Сумма: {data['amount']}₽"
    )
    await context.bot.send_message(chat_id=admin_id, text=msg)

    # Создание платежа в ЮKassa
    payment_data = {
        "amount": {"value": str(data['amount']), "currency": "RUB"},
        "confirmation": {"type": "redirect", "return_url": "https://tgbotwb.onrender.com"},
        "capture": True,
        "description": f"Оплата консультации {data['amount']} руб."
    }
    headers = {"Authorization": f"Bearer {yukassa_token}", "Content-Type": "application/json"}
    r = requests.post("https://api.yookassa.ru/v3/payments", json=payment_data, headers=headers)
    if r.status_code == 200 or r.status_code == 201:
        payment_url = r.json()['confirmation']['confirmation_url']
        await update.message.reply_text(f"Перейдите для оплаты: {payment_url}")
    else:
        await update.message.reply_text("❌ Ошибка при создании платежа. Попробуйте позже.")


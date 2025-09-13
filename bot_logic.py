import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from yookassa import Configuration, Payment

# Настройки ЮKassa
Configuration.account_id = 'test_a-AT5Q8y-jV4fkRKCOYJLXkeKeg-wJzs0L-oN7udAzo'
Configuration.secret_key = 'test_a-AT5Q8y-jV4fkRKCOYJLXkeKeg-wJzs0L-oN7udAzo'

ADMIN_CHAT_ID = 1082958705

# Клавиатура для платформы
platform_kb = ReplyKeyboardMarkup(
    [
        [KeyboardButton("iOS"), KeyboardButton("Android")]
    ],
    one_time_keyboard=True,
    resize_keyboard=True
)

# Клавиатура приветствия
def main_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("💰 Купить 100₽"), KeyboardButton("💰 Купить 500₽")],
            [KeyboardButton("📞 Связаться с поддержкой")]
        ],
        resize_keyboard=True
    )

# Обработка поддержки
async def handle_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = f"Пользователь @{user.username} ({user.id}) запросил связь с поддержкой."
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)
    await update.message.reply_text("✅ Ваш запрос отправлен админу, ожидайте ответа.")

# Обработка покупки
async def handle_buy(update: Update, context: ContextTypes.DEFAULT_TYPE, amount: int):
    await update.message.reply_text(
        "Для оплаты, пожалуйста, введите ваш номер телефона:",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отправить номер телефона", request_contact=True)]],
                                         resize_keyboard=True, one_time_keyboard=True)
    )
    context.user_data['amount'] = amount

# Обработка номера телефона
async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    if contact is None:
        await update.message.reply_text("❌ Пожалуйста, отправьте контакт через кнопку.")
        return

    context.user_data['phone'] = contact.phone_number
    context.user_data['user_id'] = contact.user_id if hasattr(contact, 'user_id') else update.effective_user.id
    await update.message.reply_text("Выберите платформу вашего телефона:", reply_markup=platform_kb)

# Обработка выбора платформы и создание платежа
async def handle_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    platform = update.message.text
    context.user_data['platform'] = platform

    amount = context.user_data.get('amount')
    phone = context.user_data.get('phone')
    user_id = context.user_data.get('user_id')

    # Формируем заказ для админа
    order_text = (
        f"Новый заказ:\n"
        f"Сумма: {amount} руб.\n"
        f"Пользователь ID: {user_id}\n"
        f"Телефон: {phone}\n"
        f"Платформа: {platform}"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=order_text)

    # Создание платежа через ЮKassa
    try:
        payment = Payment.create({
            "amount": {"value": str(amount), "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": "https://tgbotwb.onrender.com"},
            "capture": True,
            "description": f"Оплата консультации {amount} руб."
        }, uuid4().hex)

        if 'confirmation' in payment:
            url = payment.confirmation.confirmation_url
            await update.message.reply_text(f"Перейдите для оплаты: {url}")
        else:
            await update.message.reply_text("❌ Не удалось создать платеж. Попробуйте позже.")
            logging.error(payment)
    except Exception as e:
        await update.message.reply_text("❌ Ошибка при создании платежа.")
        logging.error(e)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from yookassa import Configuration, Payment

# Настройка ЮKassa
Configuration.account_id = 'test_a-AT5Q8y-jV4fkRKCOYJLXkeKeg-wJzs0L-oN7udAzo'
Configuration.secret_key = 'test_a-AT5Q8y-jV4fkRKCOYJLXkeKeg-wJzs0L-oN7udAzo'

ADMIN_CHAT_ID = 1082958705

# Клавиатуры
platform_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("iOS 🍎", callback_data="platform_ios"),
     InlineKeyboardButton("Android 🤖", callback_data="platform_android")]
])

def handle_support(update: Update, context: CallbackContext):
    user = update.effective_user
    text = f"Пользователь @{user.username} ({user.id}) хочет связаться с поддержкой."
    context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)
    update.message.reply_text("Ваше сообщение отправлено администратору ✅")

def handle_buy(update: Update, context: CallbackContext, amount: int):
    context.user_data['amount'] = amount
    update.message.reply_text(
        "Введите номер телефона для оплаты:",
    )

def handle_phone(update: Update, context: CallbackContext):
    phone = update.message.contact.phone_number if update.message.contact else update.message.text
    context.user_data['phone'] = phone
    update.message.reply_text(
        "Выберите платформу вашего устройства:",
        reply_markup=platform_keyboard
    )

def handle_platform(update: Update, context: CallbackContext):
    query = update.callback_query
    platform = 'iOS' if query.data == 'platform_ios' else 'Android'
    context.user_data['platform'] = platform
    query.answer()
    query.edit_message_text(text=f"Вы выбрали: {platform}\nГенерируем платёж...")
    create_payment(update, context)

def create_payment(update: Update, context: CallbackContext):
    amount = context.user_data['amount']
    user = update.effective_user
    phone = context.user_data['phone']
    platform = context.user_data['platform']

    payment = Payment.create({
        "amount": {
            "value": str(amount),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://tgbotwb.onrender.com"
        },
        "capture": True,
        "description": f"Оплата консультации {amount}₽"
    })

    payment_url = payment.confirmation.confirmation_url

    # Отправка ссылки пользователю
    context.bot.send_message(chat_id=user.id, text=f"Перейдите по ссылке для оплаты: {payment_url}")

    # Отправка заказа админу
    admin_text = (
        f"Новый заказ 💼\n"
        f"Имя: {user.full_name}\n"
        f"Telegram ID: {user.id}\n"
        f"Телефон: {phone}\n"
        f"Сумма: {amount}₽\n"
        f"Платформа: {platform}"
    )
    context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text)

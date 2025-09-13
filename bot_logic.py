from telegram import ReplyKeyboardMarkup, KeyboardButton, Update
from telegram.ext import ContextTypes
from yookassa import Configuration, Payment

# Настройки
ADMIN_CHAT_ID = 1082958705
YO_KASSA_TOKEN = "test_a-AT5Q8y-jV4fkRKCOYJLXkeKeg-wJzs0L-oN7udAzo"

# Настройка ЮKassa
Configuration.account_id = YO_KASSA_TOKEN.split('_')[1]
Configuration.secret_key = YO_KASSA_TOKEN

# Клавиатура выбора суммы
def get_buy_keyboard():
    keyboard = [
        [KeyboardButton("100₽"), KeyboardButton("500₽")],
        [KeyboardButton("Связь с поддержкой")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Клавиатура выбора платформы
def get_platform_keyboard():
    keyboard = [
        [KeyboardButton("iOS"), KeyboardButton("Android")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 Добро пожаловать в эксклюзивный сервис IT-консультаций!\n\n"
        "🎯 Наши консультации доступны только по рекомендации узкого круга людей.\n"
        "💼 Мы предлагаем экспертные решения для ваших IT-проблем от проверенных специалистов.\n\n"
        "💰 Стоимость консультаций:\n"
        "• 1 консультация: 100 руб.\n"
        "• 12 консультаций: 500 руб. (Вы экономите 700 руб! 🎉)\n\n"
        "Выберите опцию:"
    )
    await update.message.reply_text(welcome_text, reply_markup=get_buy_keyboard())

async def handle_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text in ["100₽", "500₽"]:
        context.user_data['amount'] = int(text.replace("₽",""))
        # Запрос номера телефона
        phone_keyboard = [[KeyboardButton("Отправить номер телефона", request_contact=True)]]
        await update.message.reply_text("Пожалуйста, введите номер телефона:", 
                                        reply_markup=ReplyKeyboardMarkup(phone_keyboard, resize_keyboard=True))
    elif text == "Связь с поддержкой":
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID,
                                       text=f"Пользователь @{update.message.from_user.username} хочет связаться с поддержкой.")
        await update.message.reply_text("Сообщение отправлено администратору ✅")

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.contact.phone_number if update.message.contact else update.message.text
    context.user_data['phone'] = phone
    context.user_data['user_id'] = update.message.from_user.id
    await update.message.reply_text("Выберите платформу вашего телефона:", reply_markup=get_platform_keyboard())

async def handle_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    platform = update.message.text
    context.user_data['platform'] = platform

    # Отправка админу
    message = (
        f"Новый заказ:\n"
        f"ID: {context.user_data['user_id']}\n"
        f"Телефон: {context.user_data['phone']}\n"
        f"Платформа: {platform}\n"
        f"Сумма: {context.user_data['amount']}₽"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)

    # Создаем платеж через ЮKassa
    payment = Payment.create({
        "amount": {
            "value": str(context.user_data['amount']),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/YourBotUsername"
        },
        "capture": True,
        "description": f"Оплата консультации {context.user_data['amount']}₽"
    }, idempotence_key=str(context.user_data['user_id']))

    # Отправляем ссылку пользователю
    await update.message.reply_text(f"Для оплаты перейдите по ссылке: {payment.confirmation.confirmation_url}")

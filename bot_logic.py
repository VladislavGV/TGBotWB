from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

ADMIN_CHAT_ID = 1082958705

async def handle_buy(update: Update, context: ContextTypes.DEFAULT_TYPE, amount: int):
    phone_keyboard = [[KeyboardButton("Ввести номер телефона", request_contact=True)]]
    await update.message.reply_text(
        f"Вы выбрали оплату {amount}₽. Пожалуйста, введите ваш номер телефона:",
        reply_markup=ReplyKeyboardMarkup(phone_keyboard, resize_keyboard=True)
    )
    context.user_data['amount'] = amount

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    context.user_data['phone'] = contact.phone_number
    context.user_data['user_id'] = update.effective_user.id

    platform_keyboard = [["iOS"], ["Android"]]
    await update.message.reply_text(
        "Выберите платформу вашего телефона:",
        reply_markup=ReplyKeyboardMarkup(platform_keyboard, resize_keyboard=True)
    )

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
    await update.message.reply_text("Спасибо! Ваш заказ отправлен, ожидайте инструкций оплаты.")

async def handle_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"Пользователь {update.effective_user.first_name} хочет связаться с поддержкой."
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)
    await update.message.reply_text("Сообщение отправлено администратору.")

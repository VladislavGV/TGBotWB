import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler, CallbackQueryHandler
from bot_logic import handle_buy, handle_support, handle_platform, handle_phone

BOT_TOKEN = "8286347628:AAGn1jX3jB-gnVESPRZlmEeoWg9IFhRnw6M"
ADMIN_CHAT_ID = 1082958705
YUKASSA_TOKEN = "test_a-AT5Q8y-jV4fkRKCOYJLXkeKeg-wJzs0L-oN7udAzo"

BUY_AMOUNT, PHONE, PLATFORM = range(3)

# Клавиатура
keyboard_main = ReplyKeyboardMarkup([
    [KeyboardButton("💳 Купить за 100₽"), KeyboardButton("💳 Купить за 500₽")],
    [KeyboardButton("📞 Связаться с техподдержкой")]
], resize_keyboard=True)

keyboard_platform = ReplyKeyboardMarkup([
    [KeyboardButton("📱 iOS"), KeyboardButton("🤖 Android")]
], resize_keyboard=True)

keyboard_phone = ReplyKeyboardMarkup([
    [KeyboardButton("📲 Ввести номер телефона", request_contact=True)]
], resize_keyboard=True)

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
    await update.message.reply_text(welcome_text, reply_markup=keyboard_main)

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_support(update, context, ADMIN_CHAT_ID)

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amount = 100 if "100" in update.message.text else 500
    context.user_data['amount'] = amount
    await update.message.reply_text("📲 Пожалуйста, отправьте ваш номер телефона:", reply_markup=keyboard_phone)
    return PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    if contact is None:
        await update.message.reply_text("❌ Пожалуйста, используйте кнопку для отправки номера телефона.")
        return PHONE
    context.user_data['phone'] = contact.phone_number
    context.user_data['user_id'] = update.message.from_user.id
    await update.message.reply_text("📱 Выберите платформу вашего телефона:", reply_markup=keyboard_platform)
    return PLATFORM

async def platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    platform_choice = update.message.text
    context.user_data['platform'] = platform_choice
    await handle_buy(update, context, ADMIN_CHAT_ID, YUKASSA_TOKEN)
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("💳 Купить за 100₽|💳 Купить за 500₽"), buy)],
        states={
            PHONE: [MessageHandler(filters.CONTACT, phone)],
            PLATFORM: [MessageHandler(filters.TEXT & ~filters.COMMAND, platform)]
        },
        fallbacks=[MessageHandler(filters.Regex("📞 Связаться с техподдержкой"), support)]
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.Regex("📞 Связаться с техподдержкой"), support))

    port = int(os.environ.get("PORT", 8000))
    application.run_polling(poll_interval=1, allowed_updates=None)

if __name__ == "__main__":
    main()

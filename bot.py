import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from bot_logic import handle_buy, handle_support, handle_phone, handle_platform, start_keyboard

TOKEN = "8286347628:AAGn1jX3jB-gnVESPRZlmEeoWg9IFhRnw6M"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

PHONE, PLATFORM = range(2)

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
    await update.message.reply_text(welcome_text, reply_markup=start_keyboard())

async def buy100(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_buy(update, context, 100)
    return PHONE

async def buy500(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_buy(update, context, 500)
    return PHONE

async def phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_phone(update, context)
    return PLATFORM

async def platform_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_platform(update, context)
    return ConversationHandler.END

async def support_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_support(update, context)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            MessageHandler(filters.Regex('^💳 100₽$'), buy100),
            MessageHandler(filters.Regex('^💳 500₽$'), buy500),
            MessageHandler(filters.Regex('^🛠 Связаться с поддержкой$'), support_handler)
        ],
        states={
            PHONE: [MessageHandler(filters.CONTACT, phone_handler)],
            PLATFORM: [MessageHandler(filters.TEXT & ~filters.COMMAND, platform_handler)],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    print("Bot started!")
    app.run_polling()

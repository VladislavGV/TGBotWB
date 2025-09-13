import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from bot_logic import handle_buy, handle_support, handle_phone, handle_platform

# Логи
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8286347628:AAGn1jX3jB-gnVESPRZlmEeoWg9IFhRnw6M"

# Основная клавиатура
main_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("💰 Купить 100₽", callback_data="buy_100")],
    [InlineKeyboardButton("💎 Купить 500₽", callback_data="buy_500")],
    [InlineKeyboardButton("🛠 Связь с поддержкой", callback_data="support")]
])

# Старт
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
    await update.message.reply_text(welcome_text, reply_markup=main_keyboard)

# Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "support":
        await handle_support(update, context)
    elif data == "buy_100":
        await handle_buy(update, context, 100)
    elif data == "buy_500":
        await handle_buy(update, context, 500)
    elif data.startswith("platform_"):
        await handle_platform(update, context)

# Обработка номера телефона
async def phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_phone(update, context)

# Основной запуск
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT | filters.CONTACT, phone_handler))

    # Запуск webhook (Render)
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("bot:app", host="0.0.0.0", port=port)

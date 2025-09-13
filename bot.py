import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from bot_logic import main_keyboard, handle_buy, handle_support, handle_phone, handle_platform
from uuid import uuid4

TOKEN = "8286347628:AAGn1jX3jB-gnVESPRZlmEeoWg9IFhRnw6M"

logging.basicConfig(level=logging.INFO)

app = FastAPI()
application = ApplicationBuilder().token(TOKEN).build()

# --- обязательная инициализация ---
@app.on_event("startup")
async def on_startup():
    await application.initialize()
    await application.start()

@app.on_event("shutdown")
async def on_shutdown():
    await application.stop()
    await application.shutdown()

# /start
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
    await update.message.reply_text(welcome_text, reply_markup=main_keyboard())

# Обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.Regex("💰 Купить 100₽"), lambda u, c: handle_buy(u, c, 100)))
application.add_handler(MessageHandler(filters.Regex("💰 Купить 500₽"), lambda u, c: handle_buy(u, c, 500)))
application.add_handler(MessageHandler(filters.Regex("📞 Связаться с поддержкой"), handle_support))
application.add_handler(MessageHandler(filters.CONTACT, handle_phone))
application.add_handler(MessageHandler(filters.Regex("iOS|Android"), handle_platform))

# Webhook
@app.post(f"/webhook/{TOKEN}")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}

# Healthcheck
@app.get("/health")
async def health():
    return {"status": "ok"}

# /start
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
    await update.message.reply_text(welcome_text, reply_markup=main_keyboard())

# Обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.Regex("💰 Купить 100₽"), lambda u, c: handle_buy(u, c, 100)))
application.add_handler(MessageHandler(filters.Regex("💰 Купить 500₽"), lambda u, c: handle_buy(u, c, 500)))
application.add_handler(MessageHandler(filters.Regex("📞 Связаться с поддержкой"), handle_support))
application.add_handler(MessageHandler(filters.CONTACT, handle_phone))
application.add_handler(MessageHandler(filters.Regex("iOS|Android"), handle_platform))

# FastAPI webhook
@app.post(f"/webhook/{TOKEN}")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}

# Healthcheck для Render
@app.get("/health")
async def health():
    return {"status": "ok"}

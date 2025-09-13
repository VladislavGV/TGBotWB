import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from bot_logic import handle_start, handle_buy, handle_phone, handle_platform

TOKEN = "8286347628:AAGn1jX3jB-gnVESPRZlmEeoWg9IFhRnw6M"

logging.basicConfig(level=logging.INFO)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", handle_start))
app.add_handler(MessageHandler(filters.Regex("^(100₽|500₽|Связь с поддержкой)$"), handle_buy))
app.add_handler(MessageHandler(filters.CONTACT | filters.TEXT & filters.Regex("^\+?\d+"), handle_phone))
app.add_handler(MessageHandler(filters.Regex("^(iOS|Android)$"), handle_platform))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bot:app", host="0.0.0.0", port=8000, log_level="info")

import os
import logging
from aiohttp import web
from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    filters,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TOKEN")
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", 0))
YKASSA_TOKEN = os.environ.get("YKASSA_TOKEN")

SELECTING_PACKAGE, GETTING_PHONE, GETTING_PLATFORM = range(3)

# --- Health endpoint для Render ---
async def health(request):
    return web.Response(text="OK", status=200)

# --- Start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💡 1 консультация — 100 ₽", callback_data="1")],
        [InlineKeyboardButton("📦 12 консультаций — 500 ₽ (экономия 700 ₽!)", callback_data="12")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "👋 *Добро пожаловать в эксклюзивный сервис IT-консультаций!*\n\n"
        "🎯 Предлагаем экспертные решения по IT проблемам только проверенными специалистами.\n\n"
        "💰 *Стоимость консультаций:*\n"
        "• 1 консультация: 100 ₽\n"
        "• 12 консультаций: 500 ₽ (экономия 700 ₽!)\n\n"
        "Выберите пакет ниже:"
    )
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    return SELECTING_PACKAGE

# --- Выбор пакета ---
async def package_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    package = query.data
    context.user_data['package'] = package
    await query.message.reply_text("Введите ваш номер телефона:")
    return GETTING_PHONE

# --- Ввод телефона ---
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    context.user_data['phone'] = phone

    keyboard = [[InlineKeyboardButton("iOS", callback_data="iOS")],
                [InlineKeyboardButton("Android", callback_data="Android")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите платформу:", reply_markup=reply_markup)
    return GETTING_PLATFORM

# --- Выбор платформы и отправка счёта ---
async def get_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    platform = query.data
    context.user_data['platform'] = platform

    package = context.user_data['package']
    phone = context.user_data['phone']

    if package == "1":
        title = "1 консультация IT специалиста"
        prices = [LabeledPrice("1 консультация", 10000)]
        payload = f"1|{phone}|{platform}"
    else:
        title = "12 консультаций IT специалиста"
        prices = [LabeledPrice("12 консультаций", 50000)]
        payload = f"12|{phone}|{platform}"

    await query.message.reply_invoice(
        title=title,
        description=f"IT консультации ({package})",
        payload=payload,
        provider_token=YKASSA_TOKEN,
        currency="RUB",
        prices=prices,
        start_parameter="consultation_order",
        need_phone_number=False,
        need_email=False,
        need_shipping_address=False
    )
    return ConversationHandler.END

# --- Precheckout ---
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)

# --- Успешная оплата ---
async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    payload_parts = payment.invoice_payload.split("|")
    package = "1 консультация" if payload_parts[0] == "1" else "12 консультаций"
    phone = payload_parts[1]
    platform = payload_parts[2]

    # Пользователь
    text = (
        f"✅ *Оплата прошла успешно!*\n\n"
        f"💡 *Пакет:* {package}\n"
        f"📱 *Платформа:* {platform}\n"
        f"💰 *Сумма:* {payment.total_amount / 100} ₽\n\n"
        "📝 В ближайшее время с вами свяжется наш специалист.\n"
        "Спасибо за выбор нашего сервиса!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

    # Админ
    if ADMIN_CHAT_ID:
        admin_text = (
            f"🛎️ *НОВЫЙ ЗАКАЗ*\n\n"
            f"💡 *Пакет:* {package}\n"
            f"📱 *Платформа:* {platform}\n"
            f"💰 *Сумма:* {payment.total_amount / 100} ₽\n"
            f"👤 *Пользователь:* @{update.effective_user.username or 'не указан'} (ID: {update.effective_user.id})\n"
            f"💳 *ID платежа:* {payment.provider_payment_charge_id}"
        )
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text, parse_mode="Markdown")

# --- Отмена ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Заказ отменен.", reply_markup=None)
    return ConversationHandler.END

# --- Основной запуск ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_PACKAGE: [CallbackQueryHandler(package_selection)],
            GETTING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            GETTING_PLATFORM: [CallbackQueryHandler(get_platform)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    # Webhook для Render
    from aiohttp import web
    web_app = web.Application()
    web_app.router.add_get("/health", health)
    web_app.router.add_post(f"/webhook/{TOKEN}", app.bot.webhook_handler)
    web.run_app(web_app, port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    main()

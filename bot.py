import os
import logging
import asyncio
from aiohttp import web
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, LabeledPrice
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
    PreCheckoutQueryHandler,
)

# Логирование
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Константы
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")
YKASSA_TOKEN = os.environ.get("YKASSA_TOKEN")
TOKEN = os.environ.get("TOKEN")

SELECTING_ACTION, GETTING_PHONE, GETTING_PLATFORM = range(3)


# ---------------- Бизнес-логика ---------------- #

async def send_admin_notification(context: ContextTypes.DEFAULT_TYPE, user_data: dict, payment_info, user_id: int, username: str):
    if not ADMIN_CHAT_ID:
        logger.warning("ADMIN_CHAT_ID не установлен. Уведомление администратору не отправлено.")
        return

    try:
        consultation_type = user_data.get("consultation_type", "")
        phone = user_data.get("phone", "")
        platform = user_data.get("platform", "")

        admin_message = (
            "🛎️ *НОВЫЙ ЗАКАЗ*\n\n"
            f"✅ *Услуга:* {consultation_type}\n"
            f"💰 *Сумма:* {payment_info.total_amount / 100} руб.\n"
            f"📞 *Телефон:* {phone}\n"
            f"📱 *Платформа:* {platform}\n"
            f"👤 *Пользователь:* @{username if username else 'не указан'} (ID: {user_id})\n"
            f"💳 *ID платежа:* {payment_info.provider_payment_charge_id}"
        )

        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID, text=admin_message, parse_mode="Markdown"
        )
        logger.info(f"Уведомление отправлено администратору {ADMIN_CHAT_ID}")

    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления администратору: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None:
        return ConversationHandler.END

    description = (
        "👋 Добро пожаловать в эксклюзивный сервис IT-консультаций!\n\n"
        "💰 Стоимость консультаций:\n"
        "• 1 консультация: 100 руб.\n"
        "• 12 консультаций: 500 руб. (экономия 700 руб 🎉)\n\n"
        "Выберите опцию:"
    )

    reply_keyboard = [["Купить 1 консультацию", "Купить 12 консультаций"]]
    await update.message.reply_text(
        description,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True
        ),
    )
    return SELECTING_ACTION


async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    context.user_data["consultation_type"] = text

    if text == "Купить 1 консультацию":
        context.user_data["price"] = 100
        await update.message.reply_text(
            "Вы выбрали 1 консультацию. Стоимость: 100 руб.\n\n"
            "Введите ваш номер телефона:",
            reply_markup=ReplyKeyboardRemove(),
        )
    elif text == "Купить 12 консультаций":
        context.user_data["price"] = 500
        await update.message.reply_text(
            "Вы выбрали пакет из 12 консультаций за 500 руб (скидка 700 руб 🎉).\n\n"
            "Введите ваш номер телефона:",
            reply_markup=ReplyKeyboardRemove(),
        )
    return GETTING_PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone = update.message.text
    if not phone or len(phone) < 5:
        await update.message.reply_text("Введите корректный номер телефона:")
        return GETTING_PHONE

    context.user_data["phone"] = phone
    platform_keyboard = [["iOS", "Android"]]
    await update.message.reply_text(
        "Спасибо! Теперь укажите вашу платформу:",
        reply_markup=ReplyKeyboardMarkup(
            platform_keyboard, one_time_keyboard=True, resize_keyboard=True
        ),
    )
    return GETTING_PLATFORM


async def get_platform(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    platform = update.message.text
    context.user_data["platform"] = platform

    consultation_type = context.user_data.get("consultation_type", "")
    phone = context.user_data.get("phone", "")

    if not YKASSA_TOKEN:
        await update.message.reply_text(
            "⚠️ Оплата временно недоступна. Обратитесь к администратору.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    if consultation_type == "Купить 1 консультацию":
        title = "1 консультация IT специалиста"
        description = "Разовая консультация IT специалиста"
        payload = "1_consultation"
        prices = [LabeledPrice(label="1 консультация", amount=10000)]
    else:
        title = "12 консультаций IT специалиста"
        description = "Пакет из 12 консультаций IT специалиста"
        payload = "12_consultations"
        prices = [LabeledPrice(label="12 консультаций", amount=50000)]

    payload += f"|{phone}|{platform}"

    try:
        await context.bot.send_invoice(
            chat_id=update.effective_chat.id,
            title=title,
            description=description,
            payload=payload,
            provider_token=YKASSA_TOKEN,
            currency="RUB",
            prices=prices,
            start_parameter="consultation_order",
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            is_flexible=False,
        )
        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Ошибка при отправке счета: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Не удалось создать счёт. Попробуйте позже или обратитесь к администратору.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END



async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)


async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment_info = update.message.successful_payment
    payload_parts = payment_info.invoice_payload.split("|")
    consultation_type = "1 консультация" if payload_parts[0] == "1_consultation" else "12 консультаций"
    phone = payload_parts[1] if len(payload_parts) > 1 else "не указан"
    platform = payload_parts[2] if len(payload_parts) > 2 else "не указана"

    context.user_data.update(
        {"consultation_type": consultation_type, "phone": phone, "platform": platform}
    )

    await update.message.reply_text(
        f"✅ Оплата прошла успешно!\n\n"
        f"Услуга: {consultation_type}\n"
        f"Стоимость: {payment_info.total_amount / 100} руб.\n"
        f"Телефон: {phone}\n"
        f"Платформа: {platform}\n\n"
        "С вами свяжется специалист 🤝",
        reply_markup=ReplyKeyboardRemove(),
    )

    user_id = update.effective_user.id
    username = update.effective_user.username
    await send_admin_notification(context, context.user_data, payment_info, user_id, username)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Заказ отменён.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# ---------------- Health Endpoint ---------------- #

async def health(request):
    return web.json_response({"status": "ok"})


# ---------------- Main ---------------- #

async def main():
    if not TOKEN:
        logger.error("TOKEN не найден!")
        return

    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_ACTION: [
                MessageHandler(
                    filters.Regex("^(Купить 1 консультацию|Купить 12 консультаций)$"),
                    handle_action,
                )
            ],
            GETTING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            GETTING_PLATFORM: [
                MessageHandler(filters.Regex("^(iOS|Android)$"), get_platform)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    # aiohttp сервер для healthcheck
    app = web.Application()
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080)))
    await site.start()

    # запускаем бота в этом же loop
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    logger.info("✅ Бот и health сервер запущены!")

    # держим процесс живым
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
# coding: utf-8
"""
Telegram bot для продажи IT-консультаций.
Поддерживает: проверку payload, валидацию телефона, уведомление админа,
health endpoint для хостинга (Render), стабильный polling с авто-рестартом.
"""

import os
import re
import asyncio
import logging
from typing import Optional

from aiohttp import web
from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
    LabeledPrice,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
    PreCheckoutQueryHandler,
)

# ---------- Logging ----------
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------- Conversation states ----------
SELECTING_ACTION, GETTING_PHONE, GETTING_PLATFORM = range(3)

# ---------- Environment & config ----------
# Required: TOKEN
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    logger.error("ENV TOKEN not set. Exiting.")
    raise SystemExit("TOKEN env var is required (Telegram bot token).")

# Optional but recommended: ADMIN_CHAT_ID (int)
ADMIN_CHAT_ID_RAW = os.environ.get("ADMIN_CHAT_ID")
ADMIN_CHAT_ID: Optional[int] = None
if ADMIN_CHAT_ID_RAW:
    try:
        ADMIN_CHAT_ID = int(ADMIN_CHAT_ID_RAW)
    except ValueError:
        logger.warning("ADMIN_CHAT_ID is set but not an integer; admin notifications disabled.")
        ADMIN_CHAT_ID = None

# Provider token for payments (ЮKassa)
YKASSA_TOKEN = os.environ.get("YKASSA_TOKEN")
if not YKASSA_TOKEN:
    logger.warning("YKASSA_TOKEN not set. Payment functionality will be disabled.")

# Health / web server port (Render provides PORT)
PORT = int(os.environ.get("PORT", "8080"))

# Optional whitelist (comma-separated ids) — если надо ограничить доступ
WHITELIST_RAW = os.environ.get("WHITELIST")  # e.g. "12345,67890"
WHITELIST = set()
if WHITELIST_RAW:
    for s in WHITELIST_RAW.split(","):
        s = s.strip()
        if s:
            try:
                WHITELIST.add(int(s))
            except ValueError:
                logger.warning("Invalid ID in WHITELIST: %s", s)

# Price constants (in kopecks)
PRICE_SINGLE = 10000  # 100.00 RUB
PRICE_12 = 50000      # 500.00 RUB

# Allowed payloads
VALID_PAYLOADS = {"1_consultation", "12_consultations"}

# Phone validation regex (international-ish)
PHONE_RE = re.compile(r"^\+?\d{7,15}$")

# ---------- Utility helpers ----------
def format_rub(kopecks: int) -> str:
    return f"{kopecks/100:.2f} руб."

# ---------- Admin notification ----------
async def send_admin_notification(
    context: ContextTypes.DEFAULT_TYPE,
    user_data: dict,
    payment_info,
    user_id: int,
    username: Optional[str],
) -> None:
    if not ADMIN_CHAT_ID:
        logger.info("ADMIN_CHAT_ID not configured — skipping admin notification.")
        return

    try:
        consultation_type = user_data.get("consultation_type", "не указана")
        phone = user_data.get("phone", "не указан")
        platform = user_data.get("platform", "не указана")
        amount = payment_info.total_amount if getattr(payment_info, "total_amount", None) is not None else 0
        provider_charge_id = getattr(payment_info, "provider_payment_charge_id", "неизвестно")

        admin_message = (
            "🛎️ *НОВЫЙ ЗАКАЗ*\n\n"
            f"✅ *Услуга:* {consultation_type}\n"
            f"💰 *Сумма:* {format_rub(amount)}\n"
            f"📞 *Телефон:* {phone}\n"
            f"📱 *Платформа:* {platform}\n"
            f"👤 *Пользователь:* @{username if username else 'не указан'} (ID: {user_id})\n"
            f"💳 *ID платежа:* {provider_charge_id}"
        )

        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_message,
            parse_mode=ParseMode.MARKDOWN,
        )
        logger.info("Admin notified (chat_id=%s).", ADMIN_CHAT_ID)

    except Exception as exc:
        logger.exception("Failed to send admin notification: %s", exc)

# ---------- Handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None:
        return ConversationHandler.END

    user_id = update.effective_user.id
    # Если задан whitelist, проверяем доступ
    if WHITELIST and user_id not in WHITELIST:
        await update.message.reply_text("Извините, доступ к боту ограничен.")
        logger.info("User %s blocked by whitelist.", user_id)
        return ConversationHandler.END

    description = (
        "👋 Добро пожаловать в эксклюзивный сервис IT-консультаций!\n\n"
        "🎯 Наши консультации доступны только по рекомендации узкого круга людей.\n"
        "💼 Мы предлагаем экспертные решения для ваших IT-проблем от проверенных специалистов.\n\n"
        "💰 Стоимость консультаций:\n"
        "• 1 консультация: 100 руб.\n"
        "• 12 консультаций: 500 руб. (Вы экономите 700 руб! 🎉)\n\n"
        "Выберите опцию:"
    )

    reply_keyboard = [["Купить 1 консультацию", "Купить 12 консультаций"]]
    await update.message.reply_text(
        description,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return SELECTING_ACTION

async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None:
        return ConversationHandler.END

    text = update.message.text or ""
    context.user_data.setdefault("consultation_type", text)

    if text == "Купить 1 консультацию":
        context.user_data["price"] = PRICE_SINGLE
        await update.message.reply_text(
            "Вы выбрали покупку 1 консультации. Стоимость: 100 руб.\n\n"
            "Для оформления заказа нам нужна дополнительная информация.\n\n"
            "Пожалуйста, введите ваш номер телефона (например, +79991234567):",
            reply_markup=ReplyKeyboardRemove(),
        )
    elif text == "Купить 12 консультаций":
        context.user_data["price"] = PRICE_12
        await update.message.reply_text(
            "Отличный выбор! Вы выбрали пакет из 12 консультаций со скидкой. "
            "Стоимость: 500 руб. (Вы экономите 700 руб! 🎉)\n\n"
            "Для оформления заказа нам нужна дополнительная информация.\n\n"
            "Пожалуйста, введите ваш номер телефона (например, +79991234567):",
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        await update.message.reply_text("Неизвестный выбор. Попробуйте /start.")
        return ConversationHandler.END

    return GETTING_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None:
        return ConversationHandler.END

    phone = (update.message.text or "").strip()
    if not PHONE_RE.match(phone):
        await update.message.reply_text("Введите корректный номер телефона (например, +79991234567):")
        return GETTING_PHONE

    context.user_data["phone"] = phone

    platform_keyboard = [["iOS", "Android"]]
    await update.message.reply_text(
        "Спасибо! Теперь укажите вашу платформу:",
        reply_markup=ReplyKeyboardMarkup(platform_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return GETTING_PLATFORM

async def get_platform(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None:
        return ConversationHandler.END

    platform = update.message.text or ""
    context.user_data["platform"] = platform

    consultation_type = context.user_data.get("consultation_type", "")
    phone = context.user_data.get("phone", "")

    # Проверяем наличие токена ЮKassa
    if not YKASSA_TOKEN:
        await update.message.reply_text(
            "В настоящее время оплата недоступна. Пожалуйста, попробуйте позже.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    # Подготовка счета
    if consultation_type == "Купить 1 консультацию":
        title = "1 консультация IT специалиста"
        description = "Консультация IT специалиста по рекомендации узкого круга людей"
        payload = "1_consultation"
        prices = [LabeledPrice(label="1 консультация", amount=PRICE_SINGLE)]
    else:
        title = "12 консультаций IT специалиста"
        description = "Пакет из 12 консультаций IT специалиста по рекомендации узкого круга людей"
        payload = "12_consultations"
        prices = [LabeledPrice(label="12 консультаций", amount=PRICE_12)]

    # Добавляем информацию о заказе в payload (payload ограничен в длине у Telegram)
    # Формат: "<payload>|<phone>|<platform>"
    payload_full = f"{payload}|{phone}|{platform}"

    try:
        await context.bot.send_invoice(
            chat_id=update.effective_chat.id,
            title=title,
            description=description,
            payload=payload_full,
            provider_token=YKASSA_TOKEN,
            currency="RUB",
            prices=prices,
            start_parameter="consultation_order",
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            is_flexible=False,
        )
        logger.info("Invoice sent to chat %s (payload=%s)", update.effective_chat.id, payload_full)
    except Exception as e:
        logger.exception("Error sending invoice: %s", e)
        await update.message.reply_text(
            "Произошла ошибка при создании счета. Пожалуйста, попробуйте позже.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    return ConversationHandler.END

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    if query is None:
        return

    # Защита от подмены payload
    try:
        invoice_payload = (query.invoice_payload or "").split("|")[0]
        if invoice_payload not in VALID_PAYLOADS:
            await query.answer(ok=False, error_message="Неверный плейлоад платежа.")
            logger.warning("PreCheckout rejected: invalid payload %s", invoice_payload)
            return

        await query.answer(ok=True)
    except Exception as exc:
        logger.exception("Error in precheckout_callback: %s", exc)
        try:
            await query.answer(ok=False, error_message="Произошла ошибка при обработке платежа.")
        except Exception:
            pass

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    payment_info = update.message.successful_payment
    if payment_info is None:
        return

    # payload format: "<payload>|<phone>|<platform>"
    payload_parts = (payment_info.invoice_payload or "").split("|")
    base = payload_parts[0] if len(payload_parts) > 0 else ""
    consultation_type = "1 консультация" if base == "1_consultation" else "12 консультаций"
    phone = payload_parts[1] if len(payload_parts) > 1 else "не указан"
    platform = payload_parts[2] if len(payload_parts) > 2 else "не указана"

    # сохраняем в user_data
    context.user_data.setdefault("consultation_type", consultation_type)
    context.user_data.setdefault("phone", phone)
    context.user_data.setdefault("platform", platform)

    # ответ пользователю
    await update.message.reply_text(
        "✅ Оплата прошла успешно! Ваш заказ оформлен.\n\n"
        f"Услуга: {consultation_type}\n"
        f"Стоимость: {format_rub(payment_info.total_amount)}\n"
        f"Телефон: {phone}\n"
        f"Платформа: {platform}\n\n"
        "В ближайшее время с вами свяжется наш специалист.\n\n"
        "Спасибо за выбор нашего эксклюзивного сервиса! 🤝",
        reply_markup=ReplyKeyboardRemove(),
    )

    # уведомляем админа (если есть)
    user_id = update.effective_user.id
    username = update.effective_user.username
    await send_admin_notification(context, context.user_data, payment_info, user_id, username)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message:
        await update.message.reply_text(
            "Заказ отменен. Если у вас возникли вопросы, обращайтесь за помощью.",
            reply_markup=ReplyKeyboardRemove(),
        )
    return ConversationHandler.END

# ---------- App creation ----------
def build_application() -> Application:
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_ACTION: [
                MessageHandler(filters.Regex("^(Купить 1 консультацию|Купить 12 консультаций)$"), handle_action)
            ],
            GETTING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            GETTING_PLATFORM: [MessageHandler(filters.Regex("^(iOS|Android)$"), get_platform)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="purchase_conversation",
        persistent=False,
    )

    application.add_handler(conv_handler)
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    return application

# ---------- Web health server (aiohttp) ----------
async def health_handler(request):
    return web.Response(text="OK")

def create_web_app():
    app = web.Application()
    app.router.add_get("/health", health_handler)
    return app

# ---------- Runner ----------
async def run_bot_and_web() -> None:
    application = build_application()

    # Strategy: запуск polling в фоне и отдельный aiohttp-сервер для health.
    # run_polling — асинхронная корутина, её можно запустить как задачу.
    polling_task = None
    backoff_seconds = 1

    # aiohttp web app
    web_app = create_web_app()
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)

    try:
        await site.start()
        logger.info("Health server started on port %s", PORT)

        # Цикл для устойчивого запуска polling с backoff на ошибка
        while True:
            try:
                logger.info("Starting Telegram polling...")
                polling_task = asyncio.create_task(application.run_polling())
                await polling_task  # дождёмся завершения (оно обычно блокирует)
                logger.warning("Polling finished gracefully — restarting.")
                backoff_seconds = 1  # сброс backoff если завершился нормально
            except asyncio.CancelledError:
                logger.info("Polling task cancelled; breaking.")
                break
            except Exception as exc:
                logger.exception("Polling crashed with exception: %s", exc)
                # Ждём с экспоненциальным backoff, но не больше 300 секунд
                logger.info("Restarting polling after %s seconds...", backoff_seconds)
                await asyncio.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, 300)
                continue

    finally:
        logger.info("Shutting down bot and web server...")
        try:
            if polling_task and not polling_task.done():
                polling_task.cancel()
                await asyncio.sleep(0.1)
        except Exception:
            pass
        try:
            await application.shutdown()
            await application.stop()
        except Exception:
            pass
        try:
            await runner.cleanup()
        except Exception:
            pass

# ---------- Entrypoint ----------
def main():
    logger.info("Bot starting...")
    try:
        asyncio.run(run_bot_and_web())
    except KeyboardInterrupt:
        logger.info("Interrupted by user (KeyboardInterrupt)")
    except Exception as e:
        logger.exception("Fatal error in main: %s", e)

if __name__ == "__main__":
    main()

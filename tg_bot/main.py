import logging
import os
import json
import datetime

from dotenv import load_dotenv
from datetime import date
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)

# Включим логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
TYPE, DESCRIPTION, CONTACT, CONFIRM = range(4)

# Клавиатура для выбора типа предмета
item_keyboard = [
    ["Компьютер", "Телефон"],
    ["Бытовая техника", "Другое"],
]

# Главная клавиатура
main_keyboard = [["Создать заявку"], ["Помощь"]]

load_dotenv()
BOT_TOKEN = os.getenv('token', 'no_secret_token')
# Запускаем логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)
request_data = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение и показывает главное меню"""
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Привет! Я бот для подачи заявок на ремонт.\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет справку о работе бота"""
    await update.message.reply_text(
        "ℹ️ Этот бот предназначен для подачи заявок на ремонт.\n\n"
        "Чтобы создать новую заявку:\n"
        "1. Нажмите 'Создать заявку'\n"
        "2. Выберите тип предмета\n"
        "3. Опишите проблему\n"
        "4. Укажите контактные данные\n\n"
        "Вы можете просмотреть свои заявки, нажав 'Мои заявки'"
    )


async def start_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает процесс создания заявки"""
    reply_markup = ReplyKeyboardMarkup(item_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Выберите тип предмета, который требует ремонта:",
        reply_markup=reply_markup
    )
    return TYPE


async def type_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет тип предмета и запрашивает описание проблемы"""
    user = update.message.from_user
    context.user_data['type'] = update.message.text
    logger.info("Тип предмета от %s: %s", user.first_name, update.message.text)

    await update.message.reply_text(
        "Опишите проблему как можно подробнее:",
        reply_markup=ReplyKeyboardRemove()
    )
    return DESCRIPTION


async def description_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет описание проблемы и запрашивает контактные данные"""
    user = update.message.from_user
    context.user_data['description'] = update.message.text
    logger.info("Описание проблемы от %s: %s", user.first_name, update.message.text)

    await update.message.reply_text(
        "Укажите ваши контактные данные (телефон, email или Telegram username):"
    )
    return CONTACT


async def contact_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет контактные данные и показывает подтверждение"""
    user = update.message.from_user
    context.user_data['contact'] = update.message.text
    logger.info("Контакт от %s: %s", user.first_name, update.message.text)

    # Формируем сообщение с подтверждением
    request_info = (
        "📝 Ваша заявка:\n\n"
        f"Тип предмета: {context.user_data['type']}\n"
        f"Описание проблемы: {context.user_data['description']}\n"
        f"Контактные данные: {context.user_data['contact']}\n\n"
        "Всё верно?"
    )

    reply_markup = ReplyKeyboardMarkup([["Да", "Нет"]], resize_keyboard=True)
    await update.message.reply_text(request_info, reply_markup=reply_markup)

    return CONFIRM


async def confirm_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает подтверждение заявки"""
    user = update.message.from_user
    if update.message.text.lower() == 'да':
        # Здесь можно добавить сохранение заявки в базу данных
        # или отправку уведомления администратору

        await update.message.reply_text(
            "✅ Ваша заявка принята! Мы свяжемся с вами в ближайшее время.",
            reply_markup=ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True))

        # Логирование заявки (можно заменить на запись в БД)
        logger.info(
            "Новая заявка:\n"
            f"Пользователь: {user.full_name} (ID: {user.id})\n"
            f"Тип предмета: {context.user_data['type']}\n"
            f"Описание: {context.user_data['description']}\n"
            f"Контакты: {context.user_data['contact']}")
    else:
        await update.message.reply_text(
            "❌ Заявка отменена. Вы можете создать новую заявку.",
            reply_markup=ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True))

        # Очищаем данные пользователя
        context.user_data.clear()
    request_data = context.user_data
    request_data["user"] = user.full_name
    Broadcast(request_data)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет процесс создания заявки"""
    user = update.message.from_user
    logger.info("Пользователь %s отменил создание заявки.", user.first_name)
    await update.message.reply_text(
        "❌ Создание заявки отменено.",
        reply_markup=ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    )

    # Очищаем данные пользователя
    context.user_data.clear()
    return ConversationHandler.END


'''async def show_my_requests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает заявки пользователя (заглушка)"""
    # В реальном боте здесь должна быть логика получения заявок пользователя из БД
    await update.message.reply_text(
        "📋 Ваши последние заявки:\n\n"
        "1. Ремонт компьютера - в обработке\n"
        "2. Замена экрана телефона - выполнено\n\n"
        "Здесь будет отображаться история ваших заявок.",
        reply_markup=ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    )'''


def Broadcast(slovar):
    today = date.today()
    slovar['time'] = str(today)
    with open('users.json', 'w', encoding='utf-8') as file:
        json.dump(slovar, file, ensure_ascii=False, indent=4)


def main() -> None:
    """Запуск бота"""
    # Замените 'YOUR_BOT_TOKEN' на токен вашего бота
    application = Application.builder().token(BOT_TOKEN).build()

    # Обработчик для обычных команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Обработчик для кнопки "Мои заявки"
    '''application.add_handler(MessageHandler(filters.Regex("^Мои заявки$"), show_my_requests))'''

    # Обработчик диалога создания заявки
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Создать заявку$"), start_request)],
        states={
            TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, type_received)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description_received)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_received)],
            CONFIRM: [MessageHandler(filters.Regex("^(Да|Нет)$"), confirm_request)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

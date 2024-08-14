import csv
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes,CallbackQueryHandler, CallbackContext
from datetime import datetime
import venv
import os
from flask import Flask, send_file

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Определяем этапы разговора
NAME, CLASSES, RACE, BACKGROUND = range(4)


# Функция старта
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Приветствую, Путник! Давай создадим твою анкету для D&D. Как тебя зовут?")
    return NAME


# Получаем имя
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Замечательно, " + update.message.text + "! Выбери класс своего персонажа!")
    await show_class_menu(update)
    return CLASSES


# Показываем меню выбора класса
async def show_class_menu(update: Update) -> None:
    keyboard = [
        [InlineKeyboardButton("Маг", callback_data='mag')],
        [InlineKeyboardButton("Воин", callback_data='voin')],
        [InlineKeyboardButton("Друид", callback_data='druid')],
        [InlineKeyboardButton("Жрец", callback_data='zrec')],
        [InlineKeyboardButton("Отмена", callback_data='cancel')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите класс своего персонажа:", reply_markup=reply_markup)


# Обработка выбора класса
async def get_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    selected_class = query.data
    context.user_data['classes'] = selected_class

    await query.message.reply_text(f"Вы выбрали класс: {selected_class}. Теперь выберите расу.")
    await show_race_menu(query)
    return RACE


# Отображаем меню выбора расы
async def show_race_menu(query) -> None:
    keyboard = [
        [InlineKeyboardButton("Человек", callback_data='human')],
        [InlineKeyboardButton("Эльф", callback_data='elf')],
        [InlineKeyboardButton("Дворф", callback_data='dwarf')],
        [InlineKeyboardButton("Хоббит", callback_data='hobbit')],
        [InlineKeyboardButton("Отмена", callback_data='cancel')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("Выберите расу вашего персонажа:", reply_markup=reply_markup)


# Обработка выбора расы
async def choose_race(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    race = query.data
    context.user_data['race'] = race
    await query.message.reply_text(f"Вы выбрали расу: {race}. Какая предыcтория вашего персонажа?")
    return BACKGROUND


# Получаем историю и сохраняем данные
async def get_background(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['background'] = update.message.text
    filename = f"{context.user_data['name']}_character_data.csv"

    # Сохраняем данные в CSV файл
    save_to_csv(context.user_data, filename)

    # Отправляем файл пользователю
    with open(filename, 'rb') as file:
        await update.message.reply_document(document=file)

    # Удаляем файл после отправки (по желанию)
    os.remove(filename)

    return -1  # Завершение разговора или другое состояние


def save_to_csv(data, filename):
    """Сохраняет данные в CSV файл."""
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([data['name'], data['classes'], data['race'], data['background']])


# Завершение разговора
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Диалог отменен. Если хотите начать заново, введите /start.")
    return ConversationHandler.END


def main():
    application = ApplicationBuilder().token('7247548199:AAHTI1v9Dlt3gylhoc3hr9LrH5H2QxgZGCQ').build()

    # Создайте обработчик разговора
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            CLASSES: [CallbackQueryHandler(get_class)],
            RACE: [CallbackQueryHandler(choose_race)],
            BACKGROUND: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_background)],
        },
        fallbacks=[CommandHandler('cancel', lambda update, context: update.message.reply_text("Процесс отменен."))],
    )

    application.add_handler(conv_handler)

    # Запустите бота
    application.run_polling()

if __name__ == '__main__':
    main()

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
    await update.message.reply_text("Приветствую тебя в таерне, Путник! Перед началом нового путешествия придется"
                                    "заполнить небольшую анкету. Так-с... Как тебя зовут?")
    return NAME


# Получаем имя
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Приятно познакомиться, " + update.message.text + "! Теперь выбери класс своего "
                                                                                      "персонажа!")
    await show_class_menu(update)
    return CLASSES


# Показываем меню выбора класса
async def show_class_menu(update: Update) -> None:
    keyboard = [
        [InlineKeyboardButton("'Бард' Сила: 8 Ловкость: 14 Телосложение: 12 Интеллект: 13 Мудрость: 10 Харизма: 15",
                              callback_data='bard, 8, 14, 12, 13, 10, 15')],
        [InlineKeyboardButton("'Варвар' Сила: 15 Ловкость: 13 Телосложение: 14 Интеллект: 8 Мудрость: 10 Харизма: 12",
                              callback_data='varvar, 15, 13, 14, 8, 10, 12')],
        [InlineKeyboardButton("'Воин' Сила: 15 Ловкость: 14 Телосложение: 13 Интеллект: 10 Мудрость: 8 Харизма: 12",
                              callback_data='voin, 15, 14, 13, 10, 8, 12')],
        [InlineKeyboardButton("'Волшебник' Сила: 8 Ловкость: 13 Телосложение: 10 Интеллект: 15 Мудрость: 14 Харизма: 12",
                              callback_data='volshebnic, 8, 13, 10, 15, 14, 12')],
        [InlineKeyboardButton("'Друид' Сила: 10 Ловкость: 12 Телосложение: 13 Интеллект: 14 Мудрость: 15 Харизма: 8",
                              callback_data='druid, 10, 12, 13, 14, 15, 8')],
        [InlineKeyboardButton("'Жрец' Сила: 10 Ловкость: 14 Телосложение: 8 Интеллект: 13 Мудрость: 15 Харизма: 12",
                              callback_data='zrec, 10, 14, 8, 13, 15, 12')],
        [InlineKeyboardButton("'Изобретатель' Сила: 13 Ловкость: 14 Телосложение: 12 Интеллект: 15 Мудрость: 8 Харизма: 10",
                              callback_data='izobret, 13, 14, 12, 15, 8, 10')],
        [InlineKeyboardButton("'Паладин' Сила: 15 Ловкость: 8 Телосложение: 13 Интеллект: 10 Мудрость: 12 Харизма: 14",
                              callback_data='paladin, 15, 8, 13, 10, 12, 14')],
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

    await query.message.reply_text(f"Так я сразу и подумал, по тебе видно, что ты знаток своего дела! "
                                   f"Теперь укажи расу персонажа")
    await show_race_menu(query)
    return RACE


# Отображаем меню выбора расы
async def show_race_menu(query) -> None:
    keyboard = [
        [InlineKeyboardButton("'Человек' все характеристики +1", callback_data='human, 1, 1, 1, 1, 1, 1')],
        [InlineKeyboardButton("'Эльф' ловкость +2", callback_data='elf, 0, 2, 0, 0, 0, 0')],
        [InlineKeyboardButton("'Дварф' сила +2", callback_data='dwarf, 2, 0, 0, 0, 0, 0')],
        [InlineKeyboardButton("'Гном' интеллект +2", callback_data='gnom, 0, 0, 0, 2, 0, 0')],
        [InlineKeyboardButton("'Гоблин' ловкость +2", callback_data='goblin, 0, 2, 0, 0, 0, 0')],
        [InlineKeyboardButton("'Полурослик' ловкость +2", callback_data='maxim, 0, 2, 0, 0, 0, 0')],
        [InlineKeyboardButton("'Кенку' мудрость +2", callback_data='kenku, 0, 0, 0, 0, 2, 0')],
        [InlineKeyboardButton("'Вампир' сила +2", callback_data='vimpire, 2, 0, 0, 0, 0, 0')],
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
    await query.message.reply_text(f"А теперь поведаешь ли мне, чем ты занимался до того, "
                                   f"как забрёл в мою таверну?")
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

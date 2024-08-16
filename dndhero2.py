import csv
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes, \
    CallbackQueryHandler
import os


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


NAME, CLASSES, RACE, BACKGROUND = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Приветствую тебя в таверне, Путник! Перед началом нового путешествия придется"
                                    "заполнить небольшую анкету. Так-с... Как тебя зовут?")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Приятно познакомиться, " + update.message.text + "!")
    await show_class_menu(update)
    return CLASSES


async def show_class_menu(update: Update) -> None:
    keyboard = [
        [InlineKeyboardButton("'Бард' Сила: 8 Ловкость: 14 Телосложение: 12 Интеллект: 13 Мудрость: 10 Харизма: 15",
                              callback_data='bard, 8, 14, 12, 13, 10, 15')],
        [InlineKeyboardButton("'Варвар' Сила: 15 Ловкость: 13 Телосложение: 14 Интеллект: 8 Мудрость: 10 Харизма: 12",
                              callback_data='varvar, 15, 13, 14, 8, 10, 12')],
        [InlineKeyboardButton("'Воин' Сила: 15 Ловкость: 14 Телосложение: 13 Интеллект: 10 Мудрость: 8 Харизма: 12",
                              callback_data='voin, 15, 14, 13, 10, 8, 12')],
        [InlineKeyboardButton(
            "'Волшебник' Сила: 8 Ловкость: 13 Телосложение: 10 Интеллект: 15 Мудрость: 14 Харизма: 12",
            callback_data='volshebnic, 8, 13, 10, 15, 14, 12')],
        [InlineKeyboardButton("'Друид' Сила: 10 Ловкость: 12 Телосложение: 13 Интеллект: 14 Мудрость: 15 Харизма: 8",
                              callback_data='druid, 10, 12, 13, 14, 15, 8')],
        [InlineKeyboardButton("'Жрец' Сила: 10 Ловкость: 14 Телосложение: 8 Интеллект: 13 Мудрость: 15 Харизма: 12",
                              callback_data='zrec, 10, 14, 8, 13, 15, 12')],
        [InlineKeyboardButton(
            "'Изобретатель' Сила: 13 Ловкость: 14 Телосложение: 12 Интеллект: 15 Мудрость: 8 Харизма: 10",
            callback_data='izobret, 13, 14, 12, 15, 8, 10')],
        [InlineKeyboardButton("'Паладин' Сила: 15 Ловкость: 8 Телосложение: 13 Интеллект: 10 Мудрость: 12 Харизма: 14",
                              callback_data='paladin, 15, 8, 13, 10, 12, 14')],
        [InlineKeyboardButton("Отмена", callback_data='cancel')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите класс своего персонажа:", reply_markup=reply_markup)

async def get_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    selected_class = query.data.split(', ')
    context.user_data['class'] = selected_class[0]
    context.user_data['class_attributes'] = list(map(int, selected_class[1:]))

    await query.message.reply_text(f"Так я сразу и подумал, по тебе видно, что ты знаток своего дела! "
                                   f"Теперь укажи расу персонажа")
    await show_race_menu(query)
    return RACE

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

async def choose_race(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    selected_race = query.data.split(', ')
    context.user_data['race'] = selected_race[0]
    race_attributes = list(map(int, selected_race[1:]))
    global final_attributes
    final_attributes = [class_attr + race_attr for class_attr, race_attr in
                        zip(context.user_data['class_attributes'], race_attributes)]

    await query.message.reply_text(f"А теперь поведаешь ли мне, чем ты занимался до того, "
                                   f"как забрёл в мою таверну?")
    return BACKGROUND


async def get_background(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['background'] = update.message.text

    name = context.user_data.get('name')
    filename = f"{name}_character_data.csv"
    save_character_to_csv(context.user_data['name'], context.user_data['race'], context.user_data['class'],
                          final_attributes, filename)
    with open(filename, 'rb') as file:
        await update.message.reply_document(document=file)

    os.remove(filename)

    return -1


def save_character_to_csv(name, race, character_class, attributes, filename='characters.csv'):
    print(f"Saving character: {name}, {race}, {character_class}, {attributes}")
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([name, race, character_class] + attributes)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Диалог отменен. Если хотите начать заново, введите /start.")
    return ConversationHandler.END


def main():
    application = ApplicationBuilder().token('7247548199:AAHTI1v9Dlt3gylhoc3hr9LrH5H2QxgZGCQ').build()

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

    application.run_polling()


if __name__ == '__main__':
    main()
